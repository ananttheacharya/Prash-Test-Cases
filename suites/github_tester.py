import httpx
import asyncio
import base64
import time

class GitHubTester:
    def __init__(self, pat, repo_name, logger):
        self.pat = pat
        self.repo_name = repo_name
        self.logger = logger
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.pat}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def run_functional_suite(self, start_from=None):
        print(f"\n--- Running Functional Suite via GitHub on {self.repo_name} ---")
        
        tests = [
            (
                "FUNC_001", "Missing Dependency", 
                ".github/workflows/func_001.yml", 
                "name: Func001\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: node src/func_001.js",
                "src/func_001.js", "const lodash = require('lodash');\nconsole.log('test');"
            ),
            (
                "FUNC_002", "Docker Build Failure", 
                ".github/workflows/func_002.yml", 
                "name: Func002\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: docker build -t test -f src/Dockerfile .",
                "src/Dockerfile", "FROM ubuntu:latest\nCOPY non_existent_file.txt /app/"
            ),
            (
                "FUNC_003", "Missing Env Var", 
                ".github/workflows/func_003.yml", 
                "name: Func003\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: python src/func_003.py",
                "src/func_003.py", "import os\napi_key = os.environ['STRIPE_SECRET_KEY']\nprint(api_key)"
            ),
            (
                "FUNC_004", "Assertion Failure", 
                ".github/workflows/func_004.yml", 
                "name: Func004\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: python src/func_004.py",
                "src/func_004.py", "def test_button():\n    expected = 'Submit'\n    received = 'Click me'\n    assert expected == received, f'Expected {expected} but got {received}'\n\ntest_button()"
            ),
            (
                "FUNC_006", "Port Conflict", 
                ".github/workflows/func_006.yml", 
                "name: Func006\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: python src/func_006.py",
                "src/func_006.py", "import socket\ns1 = socket.socket()\ns1.bind(('127.0.0.1', 3000))\ns2 = socket.socket()\ns2.bind(('127.0.0.1', 3000))"
            ),
            (
                "FUNC_016", "Gibberish Syntax", 
                ".github/workflows/func_016.yml", 
                "name: Func016\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: python src/func_016.py",
                "src/func_016.py", "asdfkjh1234987!@#$!@#$kasdfjhalksdjfhqwerqwer\nzxcvbnm,./1234"
            ),
            (
                "FUNC_018", "Non-Windows Error", 
                ".github/workflows/func_018.yml", 
                "name: Func018\non: push\njobs:\n  test:\n    runs-on: windows-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: bash -c 'echo hello'",
                "src/func_018.txt", "Just a dummy file to trigger the workflow"
            ),
            (
                "FUNC_019", "Cascading Failure", 
                ".github/workflows/func_019.yml", 
                "name: Func019\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: python src/func_019.py",
                "src/func_019.py", "import missing_pydantic\nclass BaseModel:\n    pass"
            )
        ]

        start_index = 0
        if start_from:
            for i, t in enumerate(tests):
                if t[0].upper() == start_from.upper():
                    start_index = i
                    break

        async with httpx.AsyncClient(base_url=self.api_base, headers=self.headers) as client:
            for test_args in tests[start_index:]:
                await self._run_test_case(client, *test_args)

    async def _run_test_case(self, client, test_id, desc, workflow_path, workflow_content, src_path, src_content):
        branch_name = f"test/{test_id.lower()}_{int(time.time())}"
        
        try:
            # 1. Get default branch SHA
            resp = await client.get(f"/repos/{self.repo_name}/git/refs/heads/main")
            if resp.status_code != 200:
                self.logger.log(test_id, "Functional", "GitHub API", "ERROR", f"Could not find main branch: {resp.text}")
                return
            base_sha = resp.json()["object"]["sha"]

            # 2. Create new branch
            resp = await client.post(f"/repos/{self.repo_name}/git/refs", json={
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            })
            if resp.status_code != 201:
                self.logger.log(test_id, "Functional", "GitHub API", "ERROR", f"Failed to create branch: {resp.text}")
                return
                
            self.logger.log(test_id, "Functional", branch_name, "INFO", "Branch created successfully.")

            # 3. Commit broken source file
            await self._commit_file(client, branch_name, src_path, src_content, f"Add broken {src_path}")
            
            # 4. Commit workflow file (triggers CI)
            await self._commit_file(client, branch_name, workflow_path, workflow_content, f"Add workflow {workflow_path}")
            
            self.logger.log(test_id, "Functional", branch_name, "INFO", "Broken code and workflow pushed. CI will now fail.")
            
            # 5. Monitor for PR creation (Poll every 10 seconds for up to 10 minutes)
            self.logger.log(test_id, "Functional", branch_name, "INFO", "Waiting for GitHub Action to fail and Prash to respond (Press Ctrl+C to skip this test)...")
            
            try:
                # Part A: Sense GitHub Action Status
                action_failed = False
                for _ in range(12): # Wait up to 2 mins for GitHub Action to finish
                    resp = await client.get(f"/repos/{self.repo_name}/actions/runs?branch={branch_name}")
                    if resp.status_code == 200:
                        runs = resp.json().get("workflow_runs", [])
                        any_failed = any(r.get("conclusion") == "failure" for r in runs)
                        all_completed = all(r.get("status") == "completed" for r in runs) if runs else False
                        
                        if any_failed:
                            self.logger.log(test_id, "Functional", "GitHub CI", "PASS", "GitHub Action correctly failed.")
                            action_failed = True
                            break
                        elif runs and all_completed:
                            self.logger.log(test_id, "Functional", "GitHub CI", "FAIL", "GitHub Action passed unexpectedly!")
                            return
                    await asyncio.sleep(10)
                
                if not action_failed:
                    self.logger.log(test_id, "Functional", "GitHub CI", "FAIL", "Could not detect GitHub Action failure.")
                    return

                # Part B: Wait for Prash to open PR
                self.logger.log(test_id, "Functional", branch_name, "INFO", "CI failed. Waiting up to 8 mins for Prash PR (Ctrl+C to skip)...")
                pr_opened = False
                for _ in range(48):
                    resp = await client.get(f"/repos/{self.repo_name}/pulls?state=open")
                    if resp.status_code == 200:
                        prs = resp.json()
                        for pr in prs:
                            if pr["head"]["ref"].startswith("drufiy/fix-run-") and branch_name in pr.get("body", ""):
                                pr_opened = True
                                self.logger.log(test_id, "Functional", "Prash PR", "PASS", f"Prash successfully opened PR #{pr['number']}")
                                break
                    if pr_opened:
                        break
                    await asyncio.sleep(10)
                
                if not pr_opened:
                    self.logger.log(test_id, "Functional", "Prash PR", "FAIL", "Could not detect failure / Prash did not open a PR.")

            except KeyboardInterrupt:
                print("\n")
                self.logger.log(test_id, "Functional", "Prash PR", "FAIL", "Skipped by user - Could not detect failure.")
                await asyncio.sleep(1) # Give terminal time to flush

        except Exception as e:
            self.logger.log(test_id, "Functional", "Execution", "ERROR", str(e))

    async def _commit_file(self, client, branch, path, content, message):
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Check if the file already exists (e.g. if it was merged into main previously)
        sha = None
        check_resp = await client.get(f"/repos/{self.repo_name}/contents/{path}?ref={branch}")
        if check_resp.status_code == 200:
            sha = check_resp.json().get("sha")

        payload = {
            "message": message,
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        resp = await client.put(f"/repos/{self.repo_name}/contents/{path}", json=payload)
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to commit {path}: {resp.text}")

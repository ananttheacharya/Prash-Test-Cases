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

    async def run_functional_suite(self):
        print(f"\n--- Running Functional Suite via GitHub on {self.repo_name} ---")
        async with httpx.AsyncClient(base_url=self.api_base, headers=self.headers) as client:
            await self._run_test_case(
                client, 
                "FUNC_001", 
                "Missing Dependency", 
                ".github/workflows/func_001.yml", 
                "name: Func001\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: node src/index.js",
                "src/index.js",
                "const lodash = require('lodash');\nconsole.log(lodash.camelCase('hello world'));"
            )

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
            
            # 5. Monitor for PR creation (Poll every 10 seconds for up to 3 minutes)
            self.logger.log(test_id, "Functional", branch_name, "INFO", "Waiting for Prash to open a fix PR...")
            pr_opened = False
            for _ in range(18):
                await asyncio.sleep(10)
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
            
            if not pr_opened:
                self.logger.log(test_id, "Functional", "Prash PR", "FAIL", "Prash did not open a PR within 3 minutes.")

        except Exception as e:
            self.logger.log(test_id, "Functional", "Execution", "ERROR", str(e))

    async def _commit_file(self, client, branch, path, content, message):
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        resp = await client.put(f"/repos/{self.repo_name}/contents/{path}", json={
            "message": message,
            "content": content_b64,
            "branch": branch
        })
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to commit {path}: {resp.text}")

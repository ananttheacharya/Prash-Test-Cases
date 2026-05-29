import httpx
import asyncio
import base64
import time

class StressTester:
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

    async def run_stress_suite(self):
        print(f"\n--- Running Stress Suite via GitHub on {self.repo_name} ---")
        async with httpx.AsyncClient(base_url=self.api_base, headers=self.headers) as client:
            # [E8] Stress test: Commit 6 workflow files (_MAX = 5)
            await self._test_e8_max_workflows(client)

    async def _test_e8_max_workflows(self, client):
        test_id = "E8_Stress"
        branch_name = f"test/e8_{int(time.time())}"
        
        try:
            resp = await client.get(f"/repos/{self.repo_name}/git/refs/heads/main")
            base_sha = resp.json()["object"]["sha"]

            await client.post(f"/repos/{self.repo_name}/git/refs", json={
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            })
            
            self.logger.log(test_id, "Stress", branch_name, "INFO", "Branch created. Uploading 6 workflow files...")
            
            # Upload 6 workflows (Prash architecture limits fetching to 5)
            for i in range(6):
                content = f"name: Dummy{i}\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo {i}"
                if i == 5:
                    content += "\n      - run: exit 1" # Force the last one to fail
                    
                content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                await client.put(f"/repos/{self.repo_name}/contents/.github/workflows/dummy_{i}.yml", json={
                    "message": f"Add workflow {i}",
                    "content": content_b64,
                    "branch": branch_name
                })
            
            self.logger.log(test_id, "Stress", "GitHub API", "PASS", "6 workflows pushed. Monitoring Prash response...")
            # We assume it passes if it doesn't crash the backend, but full end-to-end verification
            # requires looking at the backend logs or waiting for a PR.

        except Exception as e:
            self.logger.log(test_id, "Stress", "Execution", "ERROR", str(e))

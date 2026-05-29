import asyncio
import httpx
import time

# [R1] & [B6] Webhook Deduplication Race Condition
# The backend deduplication checks:
# 1. SELECT count from ci_runs where ...
# 2. IF count == 0: INSERT ...
# This is not atomic. If multiple webhooks arrive simultaneously, they all read count=0
# and all proceed to INSERT, bypassing the dedupe logic and creating duplicate CI runs/PRs.

url = "http://localhost:8000/webhook/github"
payload = {
    "action": "completed",
    "workflow_run": {
        "id": int(time.time()), # Unique per run to avoid static dedupe
        "head_sha": "abcdef123456",
        "conclusion": "failure",
        "head_branch": "main",
        "name": "CI",
        "repository": {
            "id": 111,
            "name": "repo",
            "full_name": "user/repo"
        }
    }
}
headers = {"X-GitHub-Event": "workflow_run"}

async def send_webhook(client, i):
    print(f"Sending webhook {i}...")
    # Empty signature so it'll fail validation if secret is set, 
    # but the race condition exists in the logic post-validation
    try:
        response = await client.post(url, json=payload, headers=headers)
        return response.status_code
    except Exception as e:
        return str(e)

async def main():
    print("=== [R1] [B6] Webhook Deduplication Race ===")
    print("Firing 10 identical webhooks simultaneously...")
    
    async with httpx.AsyncClient() as client:
        # Fire 10 requests at the exact same time
        tasks = [send_webhook(client, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
    print(f"Results: {results}")
    print("Check the database 'ci_runs' table. If there is more than 1 entry for this run, the deduplication failed.")

if __name__ == "__main__":
    asyncio.run(main())

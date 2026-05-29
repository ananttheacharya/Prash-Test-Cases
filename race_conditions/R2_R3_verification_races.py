import asyncio
import httpx

# [R2] Verification webhooks arrive before status update
# [R3] Two verification workflow events arrive concurrently

url = "http://localhost:8000/webhook/github"
headers = {"X-GitHub-Event": "workflow_run"}

# Simulating a fix PR branch
payload_base = {
    "action": "completed",
    "workflow_run": {
        "id": 999999,
        "head_sha": "fixsha123",
        "conclusion": "success",
        "head_branch": "drufiy/fix-run-abcdefgh", # This triggers verification logic
        "name": "Lint",
        "repository": {
            "id": 111,
            "name": "repo",
            "full_name": "user/repo"
        }
    }
}

async def send_event(client, name, delay=0):
    if delay:
        await asyncio.sleep(delay)
    payload = payload_base.copy()
    payload["workflow_run"]["name"] = name
    
    print(f"Sending verification for '{name}'...")
    try:
        response = await client.post(url, json=payload, headers=headers)
        return response.status_code
    except Exception as e:
        return str(e)

async def main():
    print("=== [R2] & [R3] Verification Races ===")
    
    async with httpx.AsyncClient() as client:
        # [R3] Send two verifications concurrently to test the `append_verification_workflow` RPC
        print("\nTesting concurrent verifications [R3]...")
        tasks = [
            send_event(client, "Lint"),
            send_event(client, "Test")
        ]
        results = await asyncio.gather(*tasks)
        print(f"Results: {results}")
        print("Check if BOTH 'Lint' and 'Test' are recorded in `verification_checked_workflows`.")
        
        # [R2] We simulate sending a verification event BEFORE the run is actually marked as "fixed".
        # If the run is still "applying" or "diagnosing", how does the system handle it?
        print("\nNote on [R2]: The webhook.py handles 'applying' by allowing it, but if it arrives ")
        print("during 'diagnosing', the verification might be completely lost until the reconciler sweeps.")

if __name__ == "__main__":
    asyncio.run(main())

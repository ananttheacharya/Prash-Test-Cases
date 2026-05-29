import httpx

# [S8] Error messages leak internals in dev (FastAPI default behavior)
# [S9] Wildcard CORS methods and headers

print("=== Testing [S9] Wildcard CORS ===")
try:
    response = httpx.options("http://localhost:8000/health", headers={
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "DELETE",
        "Access-Control-Request-Headers": "X-Super-Secret"
    })
    
    print(f"Access-Control-Allow-Origin: {response.headers.get('access-control-allow-origin')}")
    print(f"Access-Control-Allow-Methods: {response.headers.get('access-control-allow-methods')}")
    print(f"Access-Control-Allow-Headers: {response.headers.get('access-control-allow-headers')}")
    
    if response.headers.get('access-control-allow-origin') == "*":
        print("[!] Wildcard CORS confirmed.")
except Exception as e:
    print(f"CORS test failed: {e}")


print("\n=== Testing [S8] Internal Error Leaks ===")
try:
    # Hitting an endpoint with intentionally bad data that might cause a 500
    # e.g., missing authorization token where it tries to parse it
    response = httpx.post("http://localhost:8000/runs/invalid-uuid/apply-fix")
    print(f"Status: {response.status_code}")
    
    if "Traceback" in response.text or "File " in response.text:
        print("[!] Server leaked stack trace in response.")
    else:
        print("Response:", response.text[:200])
except Exception as e:
    print(f"Leak test failed: {e}")

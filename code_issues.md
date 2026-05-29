# Low Priority Code & Security Issues

These issues do not have executable test scripts as they are primarily static code analysis findings, configuration errors, or architectural decisions.

### [B7] DeepSeek fallback code is dead
**Verification:** Search for `model == "deepseek"` in `kimi_client.py`. You will see it is overridden immediately to Kimi, making the Anthropic/DeepSeek client initialization dead code.

### [B10] `_sleep` reimports asyncio
**Verification:** In `processor.py` inside `_sleep`, `import asyncio` is called despite `asyncio` already being imported at the top of the file.

### [B11] Logout endpoint does nothing
**Verification:** Inspect `POST /auth/logout` in `github_oauth.py`. It returns `{"success": True}` but does not invalidate the JWT, clear cookies, or revoke the GitHub token.

### [B12] Duplicate `_update_known_good_files`
**Verification:** The exact same function `_update_known_good_files` is defined in both `webhook.py` and `reconciler.py`.

### [B13] Duplicate `_gh_headers`
**Verification:** The `_gh_headers` function is defined independently in `repos.py`, `runs.py`, and `diagnosis_agent.py`.

### [B14] `.env.example` references ANTHROPIC_API_KEY
**Verification:** The codebase has logic for Kimi and DeepSeek, but `.env.example` requests an `ANTHROPIC_API_KEY`. 

### [B15] `db.healthcheck()` is async but Supabase client is sync
**Verification:** In `db.py`, the `healthcheck` function is defined with `async def`, but all supabase operations inside it (`supabase.table().select().limit(1).execute()`) are synchronous.

### [S2] Service role key in app code
**Verification:** In `db.py`, the backend instantiates the Supabase client using `SUPABASE_SERVICE_KEY`. This bypasses Row Level Security (RLS). While standard for trusted backend environments, the key's presence means RLS offers zero protection against backend vulnerabilities (like path traversal or injection).

### [S5] 7-day JWT expiry without refresh
**Verification:** In `config.py`, `JWT_EXPIRY_HOURS = 168`. There is no token rotation or blacklist implemented. A stolen token is valid for a full week.

### [S6] GitHub token decryption key in every RPC call
**Verification:** In `auth.py`, `get_decrypted_token` passes the `jwt_secret` (acting as the PGP key) as an argument to the Supabase RPC function. Database query logs in Supabase will log this key in plaintext for every request.

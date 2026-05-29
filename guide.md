# Prash by Drufiy - Discrepancy Test Suite Guide

This repository contains intentional, targeted test cases designed to trigger the vulnerabilities, bugs, race conditions, and edge cases identified in the `system_architecture_breakdown.md`.

## Test Execution Prerequisites

The edge cases, race conditions, and some schema issue tests are now written as **Pytest** suites utilizing `unittest.mock`. This allows them to simulate complex failure modes (like GitHub outages, Supabase disconnects, and concurrent worker conflicts) without requiring you to actually break your live database or hit rate limits on GitHub.

### Setup Instructions
1. Install testing dependencies in your environment:
   ```bash
   pip install pytest pytest-asyncio httpx
   ```
2. Make sure you are in the root directory where `test-cases` and `drufiy-backend` live side-by-side (the tests automatically append `drufiy-backend` to the Python path).
3. Copy `.env.mock` variables to your environment if you are running scripts standalone.

### How to Run the Tests
To run any of the edge case or race condition Pytest files, execute:
```bash
pytest -v -s test-cases/edge_cases/E1_E6_repo_pr_disconnects.py
```
*(The `-s` flag ensures the detailed verification print statements are visible in the console.)*

## Issue Mapping

### Security & Schema Bugs (`security_and_schema/`)
- **[S1] / [B3]**: `S1_B3_jwt_key_decryption.py` - Proves JWT secret reuse decrypts GitHub tokens.
- **[S3]**: `S3_oauth_csrf.html` - Initiates OAuth flow without CSRF state parameter.
- **[S4] / [B9]**: `S4_B9_add_secret_logging.py` - Triggers the `nacl` crash and shows plaintext secrets in payload.
- **[S7]**: `S7_repo_name_injection.py` - Attempts path traversal in `repo_full_name`.
- **[S8] / [S9]**: `S8_S9_api_leaks.py` - Triggers unhandled exceptions to reveal internal stacks & checks CORS headers.
- **[B1] / [E12]**: `B1_E12_iteration_constraint_crash.sql` - Demonstrates the SQL `CHECK` constraint crash on iteration 3.
- **[B2]**: `B2_rag_column_mismatch.py` - Proves the RAG feature queries the wrong database column.
- **[B4] / [B5]**: `B4_B5_missing_columns.sql` - Highlights columns referenced in code but missing from SQL schema.

### Race Conditions (`race_conditions/`)
- **[R1] / [B6]**: `R1_B6_webhook_dedupe_race.py` - Bypasses webhook deduplication by firing identical payloads concurrently.
- **[R2] / [R3]**: `R2_R3_verification_races.py` - Fires early and concurrent CI verification events.
- **[R4] / [B8]**: `R4_B8_reconciler_conflict.py` - Starts multiple reconciler workers to observe DB conflicts.
- **[R5] / [E11]**: `R5_E11_token_expiry.py` - Mocks a long-running diagnosis that exceeds GitHub app token lifespan.

### Edge Cases (`edge_cases/`)
- **[E1] / [E6]**: `E1_E6_repo_pr_disconnects.py` - Simulates manual deletion of a repo/PR mid-pipeline.
- **[E2] / [E7]**: `E2_E7_external_outages.py` - Mocks GitHub 429 and Supabase 500 responses.
- **[E3]**: `E3_invalid_llm_json.json` - JSON payload that violates Pydantic constraints.
- **[E4]**: `E4_branch_collision.py` - Triggers a 422 branch creation collision.
- **[E5]**: `E5_pagination_limit.py` - Generates 51 mock CI runs to bypass `per_page=50`.
- **[E8]**: `E8_large_repo_mock.py` - Simulates a repository with 200+ workflow files.
- **[E9]**: `E9_non_utf8_logs.zip` - Contains invalid UTF-8 logs to test decoder resilience.
- **[E10]**: `E10_patch_generation_mock.json` - Tests LLM outputting patch diffs instead of full replacements.

### Functional Templates (`functional_tests/`)
These JSON files are mock GitHub `workflow_run` webhook payloads designed to test the agent's diagnostic abilities.
- **[FUNC-001]**: `FUNC_001_missing_dependency.json`
- **[FUNC-002]**: `FUNC_002_docker_build.json`
- **[FUNC-003]**: `FUNC_003_env_var_not_set.json`
- **[FUNC-004]**: `FUNC_004_jest_failure.json`
- **[FUNC-005]**: `FUNC_005_disk_space.json`
- **[FUNC-006]**: `FUNC_006_port_conflict.json`
- **[FUNC-016]**: `FUNC_016_gibberish_input.json`
- **[FUNC-018]**: `FUNC_018_non_windows_error.json`
- **[FUNC-019]**: `FUNC_019_cascading_failures.json`

### Low-Priority Code Issues
Refer to `code_issues.md` in the root folder for verification steps for remaining low-priority bugs (B7, B10-B15) and minor security findings (S2, S5, S6).

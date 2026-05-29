# Prash by Drufiy - Master Orchestrator Guide

This directory contains a live, end-to-end testing orchestrator. Instead of static mock files, this suite actively pushes broken code to your GitHub repository and sends malicious HTTP payloads to your live production backend to ensure vulnerabilities and agent responses are handled correctly.

## Test Execution Prerequisites

1. Install testing dependencies:
   ```bash
   pip install httpx python-dotenv
   ```
2. Your `.env.prod` must contain a valid `GITHUB_PAT` (Classic token with `repo` and `workflow` scopes), your target `TEST_REPO`, and your `PROD_BACKEND_URL`.

## How to Run the Suites

Use the master orchestrator to run specific test suites:

- `python orchestrator.py --suite functional` (Runs the live CI/CD tests via GitHub)
- `python orchestrator.py --suite security` (Fires malicious payloads at the backend)
- `python orchestrator.py --suite stress` (Tests architecture limits)
- `python orchestrator.py --suite all` (Runs everything)

---

## Issue Mapping & Test Codes

The following test IDs correspond exactly to the findings in your `system_architecture_breakdown.md` and the `Prash_Druify_Testing_Template.docx`.

### 🧪 Functional CI/CD Suite (`--suite functional`)
The orchestrator dynamically creates branches, pushes these broken workflows to GitHub, and waits for Prash to fix them.

| Test ID | Description / Vulnerability Addressed |
| :--- | :--- |
| **[FUNC_001]** | **Missing Dependency**: Pushes a Node.js script importing `lodash` without an `npm install` step. Tests Prash's ability to patch CI environments. |
| **[FUNC_002]** | **Docker Build Failure**: Pushes a Dockerfile attempting to `COPY` a non-existent file. |
| **[FUNC_003]** | **Missing Environment Variables**: Code throws an error attempting to read `STRIPE_SECRET_KEY` from the environment. |
| **[FUNC_004]** | **Assertion Failure**: Simulates a standard Jest/Pytest logical assertion failure. |
| **[FUNC_006]** | **Port Conflict**: Python script attempts to bind two sockets to port 3000 simultaneously (`EADDRINUSE`). |
| **[FUNC_016]** | **Gibberish Input**: Python script containing purely invalid syntax/garbage strings. Tests LLM hallucination resistance. |
| **[FUNC_018]** | **OS Environment Error**: GitHub runner is set to `windows-latest`, but the workflow attempts to run a `bash` script. |
| **[FUNC_019]** | **Cascading Failures**: A core import error (`missing_pydantic`) causes all subsequent code to fail. Tests if Prash targets the root cause. |

### 🔒 Security Suite (`--suite security`)
Fires HTTP requests directly at the `PROD_BACKEND_URL` to test vulnerabilities.

| Test ID | Description / Vulnerability Addressed |
| :--- | :--- |
| **[S4_B9]** | **Secret Logging & NaCl Crash**: Sends plaintext secrets to the `/add-secret` endpoint to verify if the server logs them in plaintext (S4) or crashes due to missing PyNaCl (B9). |
| **[S7]** | **Webhook Path Traversal**: Sends a malformed GitHub webhook payload with a `full_name` of `../../../user/keys` to test URL construction. |
| **[S8_S9]** | **CORS & Tracebacks**: Verifies wildcard CORS headers (S9) and attempts to force a 500 internal server error to check for leaked Python tracebacks (S8). |

### 📈 Stress & Limits Suite (`--suite stress`)
Tests the architectural boundaries defined in the breakdown.

| Test ID | Description / Vulnerability Addressed |
| :--- | :--- |
| **[E8_Stress]** | **File Limit Overflow**: Pushes 6 separate workflow files to the repository at once. The architecture limit (`_MAX_WORKFLOW_FILES_TO_FETCH`) is 5. Tests if the backend gracefully limits the fetch or crashes/rate-limits. |

---

### Other Non-Executable Issues
Some low-priority issues or DB configurations (like JWT Key Reuse `[S1_B3]` or Dead Code `[B7]`) cannot be automatically orchestrated. Please refer to `code_issues.md` for manual verification steps for these findings.

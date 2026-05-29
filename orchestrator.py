import argparse
import asyncio
import os
from dotenv import load_dotenv

from lib.csv_logger import CSVLogger
from suites.security_tester import run_security_tests
from suites.github_tester import GitHubTester
from suites.stress_tester import StressTester

async def main():
    parser = argparse.ArgumentParser(description="Prash Master Orchestrator")
    parser.add_argument("--suite", choices=["all", "security", "functional", "stress"], required=True, help="Which suite to run")
    parser.add_argument("--start-from", type=str, default=None, help="Which test ID to start from (e.g., FUNC_003)")
    args = parser.parse_args()

    # Load Prod Env
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env.prod"))
    
    backend_url = os.getenv("PROD_BACKEND_URL")
    pat = os.getenv("GITHUB_PAT")
    repo = os.getenv("TEST_REPO")

    if not all([backend_url, pat, repo]):
        print("ERROR: Missing required environment variables in .env.prod")
        return

    logger = CSVLogger()
    print("🚀 Initializing Master Orchestrator...")
    print(f"Backend Target: {backend_url}")
    print(f"Repository Target: {repo}\n")

    if args.suite in ["security", "all"]:
        await run_security_tests(logger, backend_url)

    if args.suite in ["functional", "all"]:
        gh_tester = GitHubTester(pat, repo, logger)
        await gh_tester.run_functional_suite(start_from=args.start_from)

    if args.suite in ["stress", "all"]:
        stress = StressTester(pat, repo, logger)
        await stress.run_stress_suite()

    print("\n✅ Run complete. Results saved to test_results.csv")

if __name__ == "__main__":
    asyncio.run(main())

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.webhook import handle_verification_event

# [E5] Repo has >50 workflow runs on fix branch

@pytest.mark.asyncio
@patch("app.webhook.httpx.AsyncClient.get")
@patch("app.webhook.supabase")
async def test_e5_pagination_limit(mock_supabase, mock_get):
    """
    Simulates a repository with 51 CI runs on the fix branch.
    The webhook handler uses `per_page=50` and does not paginate, meaning 
    it will miss the 51st run and potentially stall the verification.
    """
    # Mock supabase to return a valid ci_run
    mock_run = {"id": "123", "status": "fixed", "verification_checked_workflows": [], "repo_id": "repo"}
    mock_supabase.table().select().eq().execute.return_value.data = [mock_run]
    
    # Create 50 mock runs indicating success
    workflow_runs = []
    for i in range(50):
        workflow_runs.append({"id": i, "name": f"Job-{i}", "status": "completed", "conclusion": "success"})
        
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"total_count": 51, "workflow_runs": workflow_runs}
    # Link header indicates there is a second page
    mock_resp.headers = {"Link": '<https://api.github.com/runs?page=2>; rel="next"'}
    mock_get.return_value = mock_resp
    
    # We trigger the verification
    # If the logic doesn't paginate, it will only process 50, and since we mock them as success,
    # it might think it's completely verified, OR it might wait forever for Job-51.
    
    payload = {
        "action": "completed",
        "workflow_run": {
            "head_branch": "drufiy/fix-run-1234",
            "repository": {"full_name": "user/repo"}
        }
    }
    
    # The current logic loops over the fetched runs.
    # It checks if any are NOT success.
    # Because it only fetched 50, and all 50 are success, it will incorrectly mark it as verified,
    # completely ignoring the 51st run (which might have failed).
    
    await handle_verification_event(payload, "fake_token")
    
    # Assert that it only made ONE get request (no pagination)
    assert mock_get.call_count == 1
    
    # Assert that it updated the status to verified based on the incomplete 50-item list
    mock_supabase.table().update.assert_called_with({"status": "verified", "updated_at": pytest.ANY})
    print("\n[E5 Verified]: The system silently ignores runs beyond page 1 (50 items) and may incorrectly mark as verified.")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

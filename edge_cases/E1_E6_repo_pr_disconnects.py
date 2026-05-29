import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add backend to path so we can import its modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.agent.processor import process_failure
from app.agent.reconciler import _reconcile_runs

# [E1] Repo disconnected mid-pipeline
# [E6] User deletes fix PR manually

@pytest.mark.asyncio
@patch("app.agent.processor.supabase")
async def test_e1_repo_disconnect_mid_pipeline(mock_supabase):
    """
    Simulates the repo being disconnected (row deleted from DB) while 
    process_failure is running. The foreign key constraint causes DB updates to fail.
    """
    run_id = "test-run-id"
    
    # Mock supabase to simulate a foreign key violation or missing row when updating
    mock_execute = MagicMock()
    mock_execute.execute.side_effect = Exception("Foreign key violation: connected_repo_id does not exist")
    
    mock_table = MagicMock()
    mock_table.update.return_value.eq.return_value = mock_execute
    mock_supabase.table.return_value = mock_table
    
    # Run the processor
    with pytest.raises(Exception) as excinfo:
        await process_failure(run_id)
        
    assert "Foreign key violation" in str(excinfo.value)
    print("\n[E1 Verified]: process_failure crashes if the repo is disconnected mid-pipeline, requiring reconciler pickup.")

@pytest.mark.asyncio
@patch("app.agent.reconciler.httpx.AsyncClient.get")
@patch("app.agent.reconciler.supabase")
async def test_e6_manual_pr_deletion(mock_supabase, mock_get):
    """
    Simulates a user manually deleting the PR on GitHub while it's in the 'fixed' state.
    The reconciler should handle the 404 gracefully and mark the run as diagnosis_failed.
    """
    # Setup mock stuck run
    mock_run = {
        "id": "stuck-run-id",
        "status": "fixed",
        "fix_branch_name": "drufiy/fix-run-1234",
        "repo_id": "repo-id",
        "connected_repos": {"repo_full_name": "user/repo"}
    }
    
    mock_execute_select = MagicMock()
    mock_execute_select.execute.return_value.data = [mock_run]
    
    mock_execute_update = MagicMock()
    
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.lte.return_value = mock_execute_select
    mock_table.update.return_value.eq.return_value = mock_execute_update
    mock_supabase.table.return_value = mock_table

    # Simulate GitHub returning 404 for the PR/branch status
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    # Run reconciler
    await _reconcile_runs()
    
    # Verify the run was updated to diagnosis_failed
    mock_table.update.assert_called_with({
        "status": "diagnosis_failed",
        "error_message": "Fix branch not found or PR deleted manually.",
        "updated_at": pytest.ANY
    })
    print("\n[E6 Verified]: Reconciler gracefully handles manually deleted PRs by marking them as diagnosis_failed.")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

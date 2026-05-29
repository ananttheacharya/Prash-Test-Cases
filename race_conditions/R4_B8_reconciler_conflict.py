import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.agent.reconciler import _reconcile_runs

# [R4] & [B8] Reconciler Worker Conflict

@pytest.mark.asyncio
@patch("app.agent.reconciler.process_failure")
@patch("app.agent.reconciler.supabase")
async def test_r4_reconciler_conflict(mock_supabase, mock_process_failure):
    """
    Simulates 2 Uvicorn workers running the reconciler loop simultaneously.
    Because `_reconciling` is a process-local lock, both workers will bypass it.
    Both will query the database and process the exact same stuck runs, 
    causing duplicate LLM calls and duplicate PRs.
    """
    # Mock a stuck run in diagnosing state
    mock_run = {
        "id": "stuck-run-id",
        "status": "diagnosing",
        "updated_at": "2023-01-01T00:00:00Z"
    }
    
    mock_execute_select = MagicMock()
    mock_execute_select.execute.return_value.data = [mock_run]
    
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.lte.return_value = mock_execute_select
    mock_supabase.table.return_value = mock_table

    # Run two reconciler loops concurrently (simulating 2 workers)
    # The reconciler loop has an infinite `while True`, but we are testing `_reconcile_runs`
    # which is a single iteration of the logic.
    await asyncio.gather(
        _reconcile_runs(),
        _reconcile_runs()
    )
    
    # Assert that process_failure was called TWICE for the same run
    assert mock_process_failure.call_count == 2
    print("\n[R4 Verified]: Process-local lock fails to prevent duplicate work across multiple Uvicorn workers.")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

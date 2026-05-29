import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.agent.processor import _fetch_relevant_files, process_failure

# [E2] GitHub rate limit hit during file fetching
# [E7] Supabase outage during pipeline

@pytest.mark.asyncio
@patch("app.agent.processor.httpx.AsyncClient.get")
async def test_e2_github_rate_limit(mock_get):
    """
    Simulates GitHub returning 403 Rate Limit Exceeded during file fetching.
    The system should silently skip the rate-limited files and proceed with partial data.
    """
    # First call succeeds, second hits rate limit
    resp_success = MagicMock()
    resp_success.status_code = 200
    resp_success.json.return_value = {"content": "cHJpbnQoJ2hlbGxvJyk="} # print('hello') in base64
    
    resp_ratelimit = MagicMock()
    resp_ratelimit.status_code = 403
    resp_ratelimit.json.return_value = {"message": "API rate limit exceeded"}
    
    mock_get.side_effect = [resp_success, resp_ratelimit, resp_ratelimit]
    
    files_to_fetch = ["file1.py", "file2.py", "file3.py"]
    
    fetched = await _fetch_relevant_files(files_to_fetch, "user/repo", "sha123", "fake_token")
    
    # Should only return the first file, and not crash
    assert len(fetched) == 1
    assert fetched[0]["path"] == "file1.py"
    print("\n[E2 Verified]: System gracefully degrading when GitHub rate limits file fetching.")

@pytest.mark.asyncio
@patch("app.agent.processor.supabase")
async def test_e7_supabase_outage(mock_supabase):
    """
    Simulates Supabase going offline (network error) while process_failure is running.
    """
    # The top-level try/except catches errors and tries to update the DB to 'diagnosis_failed'
    # But if the DB is down, THAT update will also fail.
    
    mock_table = MagicMock()
    # First call (e.g. fetching run) raises connection error
    mock_table.select.side_effect = httpx.ConnectError("Network is unreachable")
    # Second call (the error handler trying to update status) also raises connection error
    mock_table.update.side_effect = httpx.ConnectError("Network is unreachable")
    mock_supabase.table.return_value = mock_table
    
    with pytest.raises(httpx.ConnectError):
        await process_failure("run-id")
        
    print("\n[E7 Verified]: Supabase outage causes process_failure to throw unhandled exception (reconciler will pick it up later).")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

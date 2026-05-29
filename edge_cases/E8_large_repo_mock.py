import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.agent.processor import _find_workflow_files

# [E8] Very large monorepo with 200+ workflow files

@pytest.mark.asyncio
@patch("app.agent.processor.httpx.AsyncClient.get")
async def test_e8_large_repo_mock(mock_get):
    """
    Simulates a repository with 250 GitHub Action workflow YAML files.
    The system should limit the downloads to _MAX_WORKFLOW_FILES_TO_FETCH (5).
    """
    # Mock directory listing with 250 YAML files
    directory_listing = []
    for i in range(250):
        directory_listing.append({"name": f"workflow-{i}.yml", "path": f".github/workflows/workflow-{i}.yml"})
        
    mock_dir_resp = MagicMock()
    mock_dir_resp.status_code = 200
    mock_dir_resp.json.return_value = directory_listing
    
    # Mock individual file fetches
    mock_file_resp = MagicMock()
    mock_file_resp.status_code = 200
    mock_file_resp.json.return_value = {"content": "Jm5hbWU6IENJ"} # &name: CI in base64
    
    # The first call is the directory listing, subsequent calls are the file fetches
    mock_get.side_effect = [mock_dir_resp] + [mock_file_resp] * 10
    
    files = await _find_workflow_files("user/repo", "fake_token")
    
    # It should only fetch 5 files maximum despite 250 being in the directory
    assert len(files) == 5
    # Call count should be 1 (directory) + 5 (files) = 6
    assert mock_get.call_count == 6
    print("\n[E8 Verified]: System successfully limits file downloads to 5, avoiding rate limits in massive monorepos.")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

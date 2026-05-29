import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.agent.pr_creator import create_fix_pr

# [E4] Fix branch name collision

@pytest.mark.asyncio
@patch("app.agent.pr_creator.httpx.AsyncClient.post")
@patch("app.agent.pr_creator.httpx.AsyncClient.get")
@patch("app.agent.pr_creator.httpx.AsyncClient.put")
async def test_e4_branch_collision(mock_put, mock_get, mock_post):
    """
    Simulates the backend trying to create a branch, but GitHub returns 422 
    Reference Already Exists. The system should append a timestamp and retry.
    """
    # Mock GET default branch ref
    mock_get_ref = MagicMock()
    mock_get_ref.status_code = 200
    mock_get_ref.json.return_value = {"object": {"sha": "base_sha123"}}
    mock_get.return_value = mock_get_ref
    
    # Mock POST branch creation
    resp_422 = MagicMock()
    resp_422.status_code = 422
    resp_422.json.return_value = {"message": "Reference already exists"}
    
    resp_201 = MagicMock()
    resp_201.status_code = 201
    
    # First attempt: 422. Second attempt: 201.
    mock_post.side_effect = [resp_422, resp_201, resp_201] # 3rd is for PR creation
    
    # Mock PUT file commit
    mock_put_resp = MagicMock()
    mock_put_resp.status_code = 200
    mock_put.return_value = mock_put_resp

    diagnosis = {
        "problem_summary": "Test",
        "root_cause": "Test",
        "fix_description": "Test",
        "category": "code",
        "confidence": 0.9,
        "files_changed": [{"path": "file.py", "new_content": "print('fixed')"}]
    }

    result = await create_fix_pr("user/repo", "fake_token", "run123", diagnosis)
    
    # Assert that the branch name was modified to include a timestamp
    assert result["branch"].startswith("drufiy/fix-run-run123-")
    assert len(result["branch"]) > len("drufiy/fix-run-run123")
    print(f"\n[E4 Verified]: Branch collision handled. Retried with branch name: {result['branch']}")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

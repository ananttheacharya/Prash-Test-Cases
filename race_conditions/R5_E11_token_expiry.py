import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../drufiy-backend')))

from app.agent.pr_creator import create_fix_pr

# [R5] & [E11] Token Expiry Mid-Pipeline

@pytest.mark.asyncio
@patch("app.agent.pr_creator.httpx.AsyncClient.post")
@patch("app.agent.pr_creator.httpx.AsyncClient.get")
@patch("app.agent.pr_creator.httpx.AsyncClient.put")
async def test_r5_token_expiry(mock_put, mock_get, mock_post):
    """
    Simulates token expiry mid-pipeline. The GitHub App token is fetched at the start 
    of the pipeline. If the pipeline takes > 1 hour (e.g. flaky test reruns), the token expires.
    We mock the GitHub API returning 401 Unauthorized during PR creation.
    """
    # Mock GET default branch ref
    mock_get_ref = MagicMock()
    mock_get_ref.status_code = 200
    mock_get_ref.json.return_value = {"object": {"sha": "base_sha123"}}
    mock_get.return_value = mock_get_ref
    
    # Mock POST branch creation (fails with 401 Unauthorized due to expired token)
    resp_401 = MagicMock()
    resp_401.status_code = 401
    resp_401.text = "Bad credentials"
    mock_post.return_value = resp_401

    diagnosis = {
        "problem_summary": "Test",
        "root_cause": "Test",
        "fix_description": "Test",
        "category": "code",
        "confidence": 0.9,
        "files_changed": [{"path": "file.py", "new_content": "print('fixed')"}]
    }

    with pytest.raises(Exception) as excinfo:
        await create_fix_pr("user/repo", "expired_token", "run123", diagnosis)
        
    assert "Failed to create fix branch" in str(excinfo.value)
    assert "401" in str(excinfo.value)
    print("\n[R5 Verified]: System crashes with AuthError if token expires before PR creation.")

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

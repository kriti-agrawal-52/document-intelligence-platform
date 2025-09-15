import os
from datetime import datetime, timezone

import pytest
import requests


@pytest.fixture
def api_base_url():
    """Get API base URL from environment or use default."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def test_user_data():
    """Test user data with timestamp to ensure uniqueness."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "testpassword123",
    }


class TestAuthenticationFlow:
    """Integration tests for the complete authentication flow."""

    def test_complete_auth_flow(self, api_base_url, test_user_data):
        """Test complete authentication flow: register -> login -> access protected -> logout."""

        # Step 1: Health check
        health_response = requests.get(f"{api_base_url}/auth/health")
        assert health_response.status_code == 200
        assert "healthy" in health_response.json()["status"]

        # Step 2: Register user
        register_response = requests.post(
            f"{api_base_url}/auth/register", json=test_user_data
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["username"] == test_user_data["username"]
        assert user_data["email"] == test_user_data["email"]
        assert user_data["is_active"] is True
        user_id = user_data["id"]

        # Step 3: Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }
        login_response = requests.post(f"{api_base_url}/auth/token", data=login_data)
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["user_id"] == user_id

        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 4: Access protected endpoint
        profile_response = requests.get(
            f"{api_base_url}/auth/users/me", headers=headers
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["id"] == user_id
        assert profile_data["username"] == test_user_data["username"]
        assert "created_at" in profile_data

        # Step 5: Update profile
        update_data = {"email": f"updated_{test_user_data['username']}@example.com"}
        update_response = requests.put(
            f"{api_base_url}/auth/users/me", json=update_data, headers=headers
        )
        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["email"] == update_data["email"]

        # Step 6: Change password
        password_change_data = {
            "current_password": test_user_data["password"],
            "new_password": "newpassword123",
        }
        password_response = requests.post(
            f"{api_base_url}/auth/users/me/change-password",
            json=password_change_data,
            headers=headers,
        )
        assert password_response.status_code == 200
        assert "Password changed successfully" in password_response.json()["message"]

        # Step 7: Logout
        logout_response = requests.post(f"{api_base_url}/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        assert "Successfully logged out" in logout_response.json()["message"]

        # Step 8: Try to access protected endpoint with logged out token
        protected_response = requests.get(
            f"{api_base_url}/auth/users/me", headers=headers
        )
        assert protected_response.status_code == 401
        assert "invalidated" in protected_response.json()["detail"]

        # Step 9: Login with new password
        new_login_data = {
            "username": test_user_data["username"],
            "password": "newpassword123",
        }
        new_login_response = requests.post(
            f"{api_base_url}/auth/token", data=new_login_data
        )
        assert new_login_response.status_code == 200

    def test_duplicate_registration_prevention(self, api_base_url, test_user_data):
        """Test that duplicate usernames and emails are prevented."""

        # Register first user
        register_response_1 = requests.post(
            f"{api_base_url}/auth/register", json=test_user_data
        )
        assert register_response_1.status_code == 201

        # Try to register with same username
        duplicate_username_data = test_user_data.copy()
        duplicate_username_data["email"] = f"different_{test_user_data['email']}"

        register_response_2 = requests.post(
            f"{api_base_url}/auth/register", json=duplicate_username_data
        )
        assert register_response_2.status_code == 400
        assert "Username already registered" in register_response_2.json()["detail"]

        # Try to register with same email
        duplicate_email_data = test_user_data.copy()
        duplicate_email_data["username"] = f"different_{test_user_data['username']}"

        register_response_3 = requests.post(
            f"{api_base_url}/auth/register", json=duplicate_email_data
        )
        assert register_response_3.status_code == 400
        assert "Email already registered" in register_response_3.json()["detail"]

    def test_invalid_credentials(self, api_base_url, test_user_data):
        """Test login with invalid credentials."""

        # Register user first
        requests.post(f"{api_base_url}/auth/register", json=test_user_data)

        # Try login with wrong password
        wrong_password_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword",
        }
        login_response = requests.post(
            f"{api_base_url}/auth/token", data=wrong_password_data
        )
        assert login_response.status_code == 401
        assert "Incorrect username or password" in login_response.json()["detail"]

        # Try login with non-existent user
        nonexistent_user_data = {
            "username": "nonexistentuser",
            "password": "somepassword",
        }
        login_response_2 = requests.post(
            f"{api_base_url}/auth/token", data=nonexistent_user_data
        )
        assert login_response_2.status_code == 401
        assert "Incorrect username or password" in login_response_2.json()["detail"]

    def test_unauthorized_access(self, api_base_url):
        """Test accessing protected endpoints without authentication."""

        # Try to access protected endpoint without token
        response_1 = requests.get(f"{api_base_url}/auth/users/me")
        assert response_1.status_code == 401

        # Try to access protected endpoint with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response_2 = requests.get(
            f"{api_base_url}/auth/users/me", headers=invalid_headers
        )
        assert response_2.status_code == 401

        # Try to access protected endpoint with malformed header
        malformed_headers = {"Authorization": "InvalidFormat token"}
        response_3 = requests.get(
            f"{api_base_url}/auth/users/me", headers=malformed_headers
        )
        assert response_3.status_code == 401

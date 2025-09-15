import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from user_auth.main import app, get_db
from user_auth.models import Base, User
from shared.auth_utils import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }

class TestAuthEndpoints:
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/auth/health")
        assert response.status_code == 200
        assert response.json() == {"status": "Auth Service is healthy!"}

    def test_user_registration(self, client, test_user_data):
        """Test user registration endpoint."""
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_user_registration_duplicate_username(self, client, test_user_data):
        """Test registration with duplicate username fails."""
        # Register first user
        client.post("/auth/register", json=test_user_data)
        
        # Try to register with same username
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        response = client.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        user_data_1 = {
            "username": "user1",
            "email": "same@example.com",
            "password": "password123"
        }
        user_data_2 = {
            "username": "user2", 
            "email": "same@example.com",
            "password": "password123"
        }
        
        # Register first user
        client.post("/auth/register", json=user_data_1)
        
        # Try to register with same email
        response = client.post("/auth/register", json=user_data_2)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_user_login(self, client, test_user_data):
        """Test user login endpoint."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/token", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data

    def test_user_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password fails."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Try login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/token", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_get_current_user(self, client, test_user_data):
        """Test getting current user profile."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "created_at" in data
        assert "last_updated" in data

    def test_update_user_profile(self, client, test_user_data):
        """Test updating user profile."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Update profile
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {
            "username": "updated_user",
            "email": "updated@example.com"
        }
        response = client.put("/auth/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updated_user"
        assert data["email"] == "updated@example.com"

    def test_change_password(self, client, test_user_data):
        """Test changing password."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Change password
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "newpassword123"
        }
        response = client.post("/auth/users/me/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
        
        # Test login with new password
        login_data = {
            "username": test_user_data["username"],
            "password": "newpassword123"
        }
        login_response = client.post("/auth/token", data=login_data)
        assert login_response.status_code == 200

    def test_logout(self, client, test_user_data):
        """Test logout endpoint."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/auth/users/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/users/me", headers=headers)
        assert response.status_code == 401

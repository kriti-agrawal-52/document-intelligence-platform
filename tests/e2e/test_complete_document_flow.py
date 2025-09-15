import io
import os
import time
from datetime import datetime, timezone

import pytest
import requests


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def test_user_data():
    """Test user data with timestamp to ensure uniqueness."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return {
        "username": f"e2euser_{timestamp}",
        "email": f"e2e_{timestamp}@example.com",
        "password": "e2epassword123",
    }


@pytest.fixture
def authenticated_user(api_base_url, test_user_data):
    """Create and authenticate a test user, return token and user data."""
    # Register user
    register_response = requests.post(
        f"{api_base_url}/auth/register", json=test_user_data
    )
    assert register_response.status_code == 201
    user_data = register_response.json()

    # Login to get token
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
    }
    login_response = requests.post(f"{api_base_url}/auth/token", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()

    return {
        "token": token_data["access_token"],
        "user_id": user_data["id"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }


@pytest.fixture
def test_image():
    """Create a simple test image file."""
    # Create a simple test image (1x1 pixel PNG)
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
    return io.BytesIO(png_data)


class TestCompleteDocumentFlow:
    """End-to-end tests for the complete document processing flow."""

    def test_complete_document_processing_flow(
        self, api_base_url, authenticated_user, test_image
    ):
        """Test the complete flow: register -> login -> upload -> process -> retrieve -> logout."""

        headers = authenticated_user["headers"]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        document_name = f"test_document_{timestamp}"

        # Step 1: Check all health endpoints
        health_endpoints = ["/auth/health", "/extract/health", "/health"]
        for endpoint in health_endpoints:
            health_response = requests.get(f"{api_base_url}{endpoint}")
            assert health_response.status_code == 200
            assert "healthy" in health_response.json()["status"].lower()

        # Step 2: Check initial documents list (should be empty)
        docs_response = requests.get(
            f"{api_base_url}/extract/documents", headers=headers
        )
        assert docs_response.status_code == 200
        initial_docs = docs_response.json()
        assert isinstance(initial_docs, list)
        initial_count = len(initial_docs)

        # Step 3: Upload document for text extraction
        files = {"image": ("test.png", test_image, "image/png")}
        data = {"image_name": document_name}

        upload_response = requests.post(
            f"{api_base_url}/extract/image_text",
            headers=headers,
            files=files,
            data=data,
        )

        # Should return 202 Accepted for async processing
        assert upload_response.status_code == 202
        upload_data = upload_response.json()
        assert "Text extracted successfully" in upload_data["message"]
        assert upload_data["image_name"] == document_name
        assert "document_id" in upload_data
        assert "extracted_text" in upload_data
        assert "s3_url" in upload_data

        document_id = upload_data["document_id"]

        # Step 4: Check documents list (should have one more document)
        docs_response = requests.get(
            f"{api_base_url}/extract/documents", headers=headers
        )
        assert docs_response.status_code == 200
        updated_docs = docs_response.json()
        assert len(updated_docs) == initial_count + 1

        # Find our document in the list
        our_doc = next(
            (doc for doc in updated_docs if doc["image_name"] == document_name), None
        )
        assert our_doc is not None
        assert our_doc["status"] in ["processing_summary", "completed"]
        assert our_doc["s3_url"] is not None

        # Step 5: Get specific document details
        doc_detail_response = requests.get(
            f"{api_base_url}/extract/document/{document_name}", headers=headers
        )
        assert doc_detail_response.status_code == 200
        doc_details = doc_detail_response.json()
        assert doc_details["document_id"] == document_id
        assert doc_details["image_name"] == document_name
        assert doc_details["extracted_text"] is not None
        assert doc_details["s3_url"] is not None
        assert doc_details["status"] in ["processing_summary", "completed"]

        # Step 6: Wait for summarization to complete (if applicable)
        # In a real scenario, we might need to wait for the background job
        max_wait_time = 60  # seconds
        wait_interval = 5  # seconds
        waited_time = 0

        while waited_time < max_wait_time:
            doc_response = requests.get(
                f"{api_base_url}/extract/document/{document_name}", headers=headers
            )
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                if doc_data["status"] == "completed" and doc_data.get("summary"):
                    print(f"Document processing completed in {waited_time} seconds")
                    break

            time.sleep(wait_interval)
            waited_time += wait_interval

        # Step 7: Verify final document state
        final_doc_response = requests.get(
            f"{api_base_url}/extract/document/{document_name}", headers=headers
        )
        assert final_doc_response.status_code == 200
        final_doc = final_doc_response.json()
        assert final_doc["image_name"] == document_name
        assert final_doc["extracted_text"] is not None
        assert final_doc["s3_url"] is not None
        # Note: Summary might not be available if SQS/summarization service is not running

        # Step 8: Test pagination on documents endpoint
        paginated_response = requests.get(
            f"{api_base_url}/extract/documents?limit=1&skip=0", headers=headers
        )
        assert paginated_response.status_code == 200
        paginated_docs = paginated_response.json()
        assert len(paginated_docs) <= 1

        # Step 9: Test user profile access still works
        profile_response = requests.get(
            f"{api_base_url}/auth/users/me", headers=headers
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["id"] == authenticated_user["user_id"]

        # Step 10: Logout
        logout_response = requests.post(f"{api_base_url}/auth/logout", headers=headers)
        assert logout_response.status_code == 200

        # Step 11: Verify token is invalidated
        post_logout_response = requests.get(
            f"{api_base_url}/auth/users/me", headers=headers
        )
        assert post_logout_response.status_code == 401

    def test_document_upload_validation(self, api_base_url, authenticated_user):
        """Test document upload validation and error handling."""

        headers = authenticated_user["headers"]

        # Test 1: Invalid file type
        text_file = io.BytesIO(b"This is not an image")
        files = {"image": ("test.txt", text_file, "text/plain")}
        data = {"image_name": "test_invalid_file"}

        response = requests.post(
            f"{api_base_url}/extract/image_text",
            headers=headers,
            files=files,
            data=data,
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

        # Test 2: Duplicate document name
        test_image = io.BytesIO(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # First upload
        files = {"image": ("test1.png", test_image, "image/png")}
        data = {"image_name": "duplicate_test"}

        response1 = requests.post(
            f"{api_base_url}/extract/image_text",
            headers=headers,
            files=files,
            data=data,
        )
        assert response1.status_code == 202

        # Second upload with same name
        test_image.seek(0)  # Reset file pointer
        files = {"image": ("test2.png", test_image, "image/png")}
        data = {"image_name": "duplicate_test"}

        response2 = requests.post(
            f"{api_base_url}/extract/image_text",
            headers=headers,
            files=files,
            data=data,
        )
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_unauthorized_document_access(self, api_base_url):
        """Test that document endpoints require authentication."""

        endpoints_to_test = [
            "/extract/documents",
            "/extract/document/test",
        ]

        for endpoint in endpoints_to_test:
            # Test without token
            response = requests.get(f"{api_base_url}{endpoint}")
            assert response.status_code == 401

            # Test with invalid token
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{api_base_url}{endpoint}", headers=headers)
            assert response.status_code == 401

        # Test upload without authentication
        test_image = io.BytesIO(b"fake image")
        files = {"image": ("test.png", test_image, "image/png")}
        data = {"image_name": "test"}

        response = requests.post(
            f"{api_base_url}/extract/image_text", files=files, data=data
        )
        assert response.status_code == 401

    def test_cross_user_document_isolation(self, api_base_url):
        """Test that users can only access their own documents."""

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Create two different users
        user1_data = {
            "username": f"user1_{timestamp}",
            "email": f"user1_{timestamp}@example.com",
            "password": "password123",
        }
        user2_data = {
            "username": f"user2_{timestamp}",
            "email": f"user2_{timestamp}@example.com",
            "password": "password123",
        }

        # Register both users
        requests.post(f"{api_base_url}/auth/register", json=user1_data)
        requests.post(f"{api_base_url}/auth/register", json=user2_data)

        # Login both users
        user1_token = requests.post(
            f"{api_base_url}/auth/token",
            data={
                "username": user1_data["username"],
                "password": user1_data["password"],
            },
        ).json()["access_token"]

        user2_token = requests.post(
            f"{api_base_url}/auth/token",
            data={
                "username": user2_data["username"],
                "password": user2_data["password"],
            },
        ).json()["access_token"]

        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # User1 uploads a document
        test_image = io.BytesIO(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        files = {"image": ("user1_doc.png", test_image, "image/png")}
        data = {"image_name": "user1_document"}

        upload_response = requests.post(
            f"{api_base_url}/extract/image_text",
            headers=user1_headers,
            files=files,
            data=data,
        )
        assert upload_response.status_code == 202

        # User1 can see their document
        user1_docs = requests.get(
            f"{api_base_url}/extract/documents", headers=user1_headers
        ).json()
        assert len(user1_docs) >= 1
        assert any(doc["image_name"] == "user1_document" for doc in user1_docs)

        # User2 cannot see user1's document
        user2_docs = requests.get(
            f"{api_base_url}/extract/documents", headers=user2_headers
        ).json()
        assert not any(doc["image_name"] == "user1_document" for doc in user2_docs)

        # User2 cannot access user1's document directly
        doc_response = requests.get(
            f"{api_base_url}/extract/document/user1_document", headers=user2_headers
        )
        assert doc_response.status_code == 404

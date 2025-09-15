import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock the dependencies before importing the main app
with patch("text_extraction.main.connect_to_mongo"), patch(
    "text_extraction.main.connect_to_redis"
), patch("shared.jwt_blacklist.init_jwt_blacklist_redis"):
    from text_extraction.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_jwt_token():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTYwMDAwMDAwMCwianRpIjoiYWJjZDEyMzQifQ.mock_signature"


@pytest.fixture
def auth_headers(mock_jwt_token):
    return {"Authorization": f"Bearer {mock_jwt_token}"}


class TestTextExtractionEndpoints:

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/extract/health")
        assert response.status_code == 200
        assert response.json() == {"status": "Text Extraction Service is healthy!"}

    @patch("shared.auth_utils.verify_token")
    @patch("text_extraction.main.get_extracted_texts_collection")
    def test_get_documents_empty_list(
        self, mock_collection, mock_verify_token, client, auth_headers
    ):
        """Test getting documents when user has no documents."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Mock empty collection
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = []
        mock_collection.return_value.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )

        response = client.get("/extract/documents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @patch("shared.auth_utils.verify_token")
    @patch("text_extraction.main.get_extracted_texts_collection")
    def test_get_documents_with_data(
        self, mock_collection, mock_verify_token, client, auth_headers
    ):
        """Test getting documents when user has documents."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Mock document data
        from datetime import datetime, timezone

        from bson import ObjectId

        mock_doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "image_name": "test_document",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "s3_url": "https://s3.amazonaws.com/bucket/test.jpg",
            "summary": "Test summary",
        }

        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [mock_doc]
        mock_collection.return_value.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )

        response = client.get("/extract/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["image_name"] == "test_document"
        assert data[0]["status"] == "completed"
        assert data[0]["has_summary"] is True

    @patch("shared.auth_utils.verify_token")
    @patch("text_extraction.main.get_extracted_texts_collection")
    def test_get_document_by_name_not_found(
        self, mock_collection, mock_verify_token, client, auth_headers
    ):
        """Test getting a document that doesn't exist."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Mock document not found
        mock_collection.return_value.find_one.return_value = None

        response = client.get("/extract/document/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    @patch("shared.auth_utils.verify_token")
    @patch("text_extraction.main.get_extracted_texts_collection")
    def test_get_document_by_name_success(
        self, mock_collection, mock_verify_token, client, auth_headers
    ):
        """Test getting a document successfully."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Mock document data
        from datetime import datetime, timezone

        from bson import ObjectId

        mock_doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "image_name": "test_document",
            "status": "completed",
            "extracted_text": "This is extracted text",
            "summary": "This is a summary",
            "s3_url": "https://s3.amazonaws.com/bucket/test.jpg",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        mock_collection.return_value.find_one.return_value = mock_doc

        response = client.get("/extract/document/test_document", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["image_name"] == "test_document"
        assert data["status"] == "completed"
        assert data["extracted_text"] == "This is extracted text"
        assert data["summary"] == "This is a summary"

    @patch("shared.auth_utils.verify_token")
    @patch("text_extraction.main.get_extracted_texts_collection")
    @patch("text_extraction.main.openai_client")
    @patch("text_extraction.main.s3_client")
    @patch("text_extraction.main.sqs_client")
    @patch("text_extraction.main.cache_user_recent_extractions")
    def test_extract_text_success(
        self,
        mock_cache,
        mock_sqs,
        mock_s3,
        mock_openai,
        mock_collection,
        mock_verify_token,
        client,
        auth_headers,
    ):
        """Test successful text extraction from image."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Mock no existing document
        mock_collection.return_value.find_one.return_value = None

        # Mock successful database insert
        from bson import ObjectId

        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439011")
        mock_collection.return_value.insert_one.return_value = mock_insert_result
        mock_collection.return_value.update_one.return_value = None

        # Mock S3 upload
        mock_s3.put_object.return_value = None

        # Mock OpenAI response
        mock_openai_response = MagicMock()
        mock_openai_response.choices[0].message.content = "Extracted text from image"
        mock_openai.chat.completions.create.return_value = mock_openai_response

        # Mock SQS
        mock_sqs.send_message.return_value = None

        # Mock cache
        mock_cache.return_value = None

        # Create test image file
        test_image = io.BytesIO(b"fake image content")

        response = client.post(
            "/extract/image_text",
            headers=auth_headers,
            files={"image": ("test.jpg", test_image, "image/jpeg")},
            data={"image_name": "test_document"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "Text extracted successfully" in data["message"]
        assert data["image_name"] == "test_document"
        assert data["extracted_text"] == "Extracted text from image"
        assert "s3_url" in data

    @patch("shared.auth_utils.verify_token")
    def test_extract_text_invalid_file_type(
        self, mock_verify_token, client, auth_headers
    ):
        """Test text extraction with invalid file type."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Create test non-image file
        test_file = io.BytesIO(b"not an image")

        response = client.post(
            "/extract/image_text",
            headers=auth_headers,
            files={"image": ("test.txt", test_file, "text/plain")},
            data={"image_name": "test_document"},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    @patch("shared.auth_utils.verify_token")
    @patch("text_extraction.main.get_extracted_texts_collection")
    def test_extract_text_duplicate_name(
        self, mock_collection, mock_verify_token, client, auth_headers
    ):
        """Test text extraction with duplicate document name."""
        # Mock authentication
        mock_verify_token.return_value = 123

        # Mock existing document
        mock_collection.return_value.find_one.return_value = {
            "image_name": "test_document"
        }

        # Create test image file
        test_image = io.BytesIO(b"fake image content")

        response = client.post(
            "/extract/image_text",
            headers=auth_headers,
            files={"image": ("test.jpg", test_image, "image/jpeg")},
            data={"image_name": "test_document"},
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/extract/documents")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/extract/documents", headers=headers)
        assert response.status_code == 401

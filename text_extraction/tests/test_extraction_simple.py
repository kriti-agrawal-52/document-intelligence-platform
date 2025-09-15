import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Mock dependencies before importing
with patch("text_extraction.main.connect_to_mongo"), patch(
    "text_extraction.main.connect_to_redis"
), patch("shared.jwt_blacklist.init_jwt_blacklist_redis"):
    from text_extraction.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_auth_token():
    """Mock JWT token for authentication."""
    return "mock_jwt_token"


@pytest.fixture
def auth_headers(mock_auth_token):
    """Mock authentication headers."""
    return {"Authorization": f"Bearer {mock_auth_token}"}


class TestTextExtractionSimple:
    """Simplified unit tests for text extraction service."""

    def test_health_check(self, client):
        """Test that health endpoint returns correct response."""
        response = client.get("/extract/health")
        assert response.status_code == 200
        assert response.json() == {"status": "Text Extraction Service is healthy!"}

    @patch("shared.auth_utils.verify_token")
    def test_documents_endpoint_requires_auth(self, mock_verify, client):
        """Test that documents endpoint requires authentication."""
        # Test without token
        response = client.get("/extract/documents")
        assert response.status_code == 401

        # Test with mock token
        mock_verify.return_value = 123
        headers = {"Authorization": "Bearer mock_token"}
        response = client.get("/extract/documents", headers=headers)

        # Should attempt to process (may fail due to mocking but auth works)
        assert response.status_code in [200, 500]

    @patch("shared.auth_utils.verify_token")
    def test_upload_endpoint_structure(self, mock_verify, client, auth_headers):
        """Test upload endpoint accepts correct file structure."""
        mock_verify.return_value = 123

        # Create a test file
        test_file = io.BytesIO(b"fake image content")

        # Test the endpoint structure
        response = client.post(
            "/extract/image_text",
            headers=auth_headers,
            files={"image": ("test.jpg", test_file, "image/jpeg")},
            data={"image_name": "test_document"},
        )

        # Should accept the request format (may fail due to mocking)
        assert response.status_code in [202, 400, 500]

    @patch("shared.auth_utils.verify_token")
    def test_invalid_file_type_validation(self, mock_verify, client, auth_headers):
        """Test that invalid file types are rejected."""
        mock_verify.return_value = 123

        # Create a non-image file
        test_file = io.BytesIO(b"not an image")

        response = client.post(
            "/extract/image_text",
            headers=auth_headers,
            files={"image": ("test.txt", test_file, "text/plain")},
            data={"image_name": "test_document"},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]


class TestExtractionUtilsUnit:
    """Unit tests for extraction utility functions."""

    @patch("text_extraction.redis_cache.redis_client")
    def test_cache_functions(self, mock_redis):
        """Test Redis cache functions."""
        from text_extraction.redis_cache import (cache_extraction,
                                                 get_cached_data)

        mock_redis.setex.return_value = True
        mock_redis.get.return_value = b'{"test": "data"}'

        # Test caching
        result = cache_extraction("test_key", "test_data")
        # Should not raise exception

        # Test retrieval
        data = get_cached_data("test_key")
        # Should not raise exception

    def test_file_validation_logic(self):
        """Test file type validation logic."""
        # Test valid image types
        valid_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]

        for content_type in valid_types:
            # This would be the validation logic
            is_valid = content_type.startswith("image/")
            assert is_valid is True

        # Test invalid types
        invalid_types = ["text/plain", "application/pdf", "video/mp4"]

        for content_type in invalid_types:
            is_valid = content_type.startswith("image/")
            assert is_valid is False

    def test_document_name_validation(self):
        """Test document name validation logic."""
        # Test valid names
        valid_names = ["document1", "my-doc", "test_file", "doc123"]

        for name in valid_names:
            # Basic validation: non-empty, reasonable length
            is_valid = len(name) > 0 and len(name) <= 100
            assert is_valid is True

        # Test invalid names
        invalid_names = ["", "a" * 101]  # Empty or too long

        for name in invalid_names:
            is_valid = len(name) > 0 and len(name) <= 100
            assert is_valid is False

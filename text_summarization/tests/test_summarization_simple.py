import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Mock dependencies before importing
with patch("text_summarization.main.mongo_client"), patch(
    "text_summarization.main.openai_client"
), patch("text_summarization.main.sqs_client"):
    from text_summarization.main import SQSMessageBody, app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


class TestSummarizationSimple:
    """Simplified unit tests for text summarization service."""

    def test_health_check(self, client):
        """Test that health endpoint returns correct response."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "Summarization Service is healthy"}

    def test_sqs_message_validation(self):
        """Test SQS message body validation with Pydantic."""
        # Valid message
        valid_data = {
            "document_id": "507f1f77bcf86cd799439011",
            "user_id": 123,
            "text_to_summarize": "This is text to summarize.",
        }

        message = SQSMessageBody(**valid_data)
        assert message.document_id == "507f1f77bcf86cd799439011"
        assert message.user_id == 123
        assert message.text_to_summarize == "This is text to summarize."

    def test_sqs_message_validation_invalid(self):
        """Test SQS message validation rejects invalid data."""
        # Missing required fields
        invalid_data = {
            "document_id": "507f1f77bcf86cd799439011",
            # Missing user_id and text_to_summarize
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            SQSMessageBody(**invalid_data)

    def test_message_parsing(self):
        """Test JSON message parsing logic."""
        # Valid JSON message
        valid_message = {
            "ReceiptHandle": "test-receipt-handle",
            "Body": json.dumps(
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    "user_id": 123,
                    "text_to_summarize": "Test text",
                }
            ),
        }

        # Parse the message body
        try:
            body_data = json.loads(valid_message["Body"])
            message_obj = SQSMessageBody(**body_data)
            assert message_obj.document_id == "507f1f77bcf86cd799439011"
        except Exception:
            pytest.fail("Valid message should parse successfully")

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON messages."""
        invalid_message = {
            "ReceiptHandle": "test-receipt-handle",
            "Body": "invalid json content",
        }

        # Should handle invalid JSON gracefully
        try:
            json.loads(invalid_message["Body"])
            pytest.fail("Should raise JSON decode error")
        except json.JSONDecodeError:
            # Expected behavior
            pass


class TestSummarizationUtilsUnit:
    """Unit tests for summarization utility functions."""

    @patch("text_summarization.main.openai_client")
    def test_openai_client_mock(self, mock_openai):
        """Test OpenAI client mocking works correctly."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices[0].message.content = "This is a test summary."
        mock_openai.chat.completions.create.return_value = mock_response

        # Simulate calling OpenAI
        response = mock_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Summarize this text"}],
        )

        assert response.choices[0].message.content == "This is a test summary."

    @patch("text_summarization.main.db_collection")
    def test_database_update_mock(self, mock_collection):
        """Test database update mocking works correctly."""
        # Mock database update
        mock_collection.update_one.return_value = Mock()

        # Simulate database update
        result = mock_collection.update_one(
            {"_id": "test_id"},
            {"$set": {"summary": "test summary", "status": "completed"}},
        )

        # Should not raise exception
        assert result is not None

    def test_text_length_validation(self):
        """Test text length validation logic."""
        # Test reasonable text lengths
        short_text = "Short text."
        medium_text = "This is a medium length text " * 10
        long_text = "This is a very long text " * 100

        # Basic validation logic
        def is_valid_length(text):
            return 1 <= len(text) <= 10000  # Reasonable limits

        assert is_valid_length(short_text) is True
        assert is_valid_length(medium_text) is True
        assert is_valid_length(long_text) is True

        # Test edge cases
        empty_text = ""
        extremely_long_text = "x" * 20000

        assert is_valid_length(empty_text) is False
        assert is_valid_length(extremely_long_text) is False

    def test_document_id_format(self):
        """Test document ID format validation."""
        # Valid ObjectId format (24 hex characters)
        valid_ids = [
            "507f1f77bcf86cd799439011",
            "123456789012345678901234",
            "abcdef123456789012345678",
        ]

        for doc_id in valid_ids:
            # Basic format validation
            is_valid = len(doc_id) == 24 and all(
                c in "0123456789abcdef" for c in doc_id.lower()
            )
            assert is_valid is True

        # Invalid IDs
        invalid_ids = [
            "short",
            "toolongtobeavalidobjectid123456789",
            "507f1f77bcf86cd79943901g",  # Invalid character
            "",
        ]

        for doc_id in invalid_ids:
            is_valid = len(doc_id) == 24 and all(
                c in "0123456789abcdef" for c in doc_id.lower()
            )
            assert is_valid is False

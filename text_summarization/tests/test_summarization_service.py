import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock the dependencies before importing the main app
with patch("text_summarization.main.mongo_client"), patch(
    "text_summarization.main.openai_client"
), patch("text_summarization.main.sqs_client"):
    from text_summarization.main import SQSMessageBody, app, process_message


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestSummarizationService:

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "Summarization Service is healthy"}

    @patch("text_summarization.main.openai_client")
    @patch("text_summarization.main.db_collection")
    @patch("text_summarization.main.sqs_client")
    async def test_process_message_success(self, mock_sqs, mock_db, mock_openai):
        """Test successful processing of SQS message."""
        # Mock SQS message
        message = {
            "ReceiptHandle": "test-receipt-handle",
            "Body": json.dumps(
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    "user_id": 123,
                    "text_to_summarize": "This is a long text that needs to be summarized.",
                }
            ),
        }

        # Mock OpenAI response
        mock_openai_response = MagicMock()
        mock_openai_response.choices[0].message.content = (
            "This is a summary of the text."
        )
        mock_openai.chat.completions.create.return_value = mock_openai_response

        # Mock database update
        mock_db.update_one.return_value = None

        # Mock SQS delete
        mock_sqs.delete_message.return_value = None

        # Process the message
        await process_message(message)

        # Verify OpenAI was called
        mock_openai.chat.completions.create.assert_called_once()

        # Verify database was updated
        mock_db.update_one.assert_called_once()

        # Verify SQS message was deleted
        mock_sqs.delete_message.assert_called_once()

    @patch("text_summarization.main.openai_client")
    @patch("text_summarization.main.db_collection")
    @patch("text_summarization.main.sqs_client")
    async def test_process_message_invalid_json(self, mock_sqs, mock_db, mock_openai):
        """Test processing of SQS message with invalid JSON."""
        # Mock SQS message with invalid JSON
        message = {"ReceiptHandle": "test-receipt-handle", "Body": "invalid json"}

        # Process the message (should not raise exception)
        await process_message(message)

        # Verify OpenAI was not called
        mock_openai.chat.completions.create.assert_not_called()

        # Verify database was not updated
        mock_db.update_one.assert_not_called()

        # Verify SQS message was not deleted
        mock_sqs.delete_message.assert_not_called()

    @patch("text_summarization.main.openai_client")
    @patch("text_summarization.main.db_collection")
    @patch("text_summarization.main.sqs_client")
    async def test_process_message_missing_fields(self, mock_sqs, mock_db, mock_openai):
        """Test processing of SQS message with missing required fields."""
        # Mock SQS message with missing fields
        message = {
            "ReceiptHandle": "test-receipt-handle",
            "Body": json.dumps(
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    # Missing user_id and text_to_summarize
                }
            ),
        }

        # Process the message (should not raise exception)
        await process_message(message)

        # Verify OpenAI was not called
        mock_openai.chat.completions.create.assert_not_called()

        # Verify database was not updated
        mock_db.update_one.assert_not_called()

        # Verify SQS message was not deleted
        mock_sqs.delete_message.assert_not_called()

    @patch("text_summarization.main.openai_client")
    @patch("text_summarization.main.db_collection")
    @patch("text_summarization.main.sqs_client")
    async def test_process_message_openai_error(self, mock_sqs, mock_db, mock_openai):
        """Test processing when OpenAI API fails."""
        # Mock SQS message
        message = {
            "ReceiptHandle": "test-receipt-handle",
            "Body": json.dumps(
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    "user_id": 123,
                    "text_to_summarize": "This is a long text that needs to be summarized.",
                }
            ),
        }

        # Mock OpenAI error
        mock_openai.chat.completions.create.side_effect = Exception("OpenAI API error")

        # Process the message (should not raise exception)
        await process_message(message)

        # Verify OpenAI was called
        mock_openai.chat.completions.create.assert_called_once()

        # Verify database was not updated due to error
        mock_db.update_one.assert_not_called()

        # Verify SQS message was not deleted due to error
        mock_sqs.delete_message.assert_not_called()

    @patch("text_summarization.main.openai_client")
    @patch("text_summarization.main.db_collection")
    @patch("text_summarization.main.sqs_client")
    async def test_process_message_database_error(self, mock_sqs, mock_db, mock_openai):
        """Test processing when database update fails."""
        # Mock SQS message
        message = {
            "ReceiptHandle": "test-receipt-handle",
            "Body": json.dumps(
                {
                    "document_id": "507f1f77bcf86cd799439011",
                    "user_id": 123,
                    "text_to_summarize": "This is a long text that needs to be summarized.",
                }
            ),
        }

        # Mock OpenAI response
        mock_openai_response = MagicMock()
        mock_openai_response.choices[0].message.content = (
            "This is a summary of the text."
        )
        mock_openai.chat.completions.create.return_value = mock_openai_response

        # Mock database error
        mock_db.update_one.side_effect = Exception("Database error")

        # Process the message (should not raise exception)
        await process_message(message)

        # Verify OpenAI was called
        mock_openai.chat.completions.create.assert_called_once()

        # Verify database update was attempted
        mock_db.update_one.assert_called_once()

        # Verify SQS message was not deleted due to error
        mock_sqs.delete_message.assert_not_called()

    def test_sqs_message_body_validation(self):
        """Test SQS message body validation."""
        # Valid message body
        valid_body = {
            "document_id": "507f1f77bcf86cd799439011",
            "user_id": 123,
            "text_to_summarize": "This is text to summarize.",
        }

        message = SQSMessageBody(**valid_body)
        assert message.document_id == "507f1f77bcf86cd799439011"
        assert message.user_id == 123
        assert message.text_to_summarize == "This is text to summarize."

    def test_sqs_message_body_validation_invalid(self):
        """Test SQS message body validation with invalid data."""
        # Invalid message body (missing required fields)
        invalid_body = {
            "document_id": "507f1f77bcf86cd799439011",
            # Missing user_id and text_to_summarize
        }

        with pytest.raises(Exception):  # Pydantic validation error
            SQSMessageBody(**invalid_body)

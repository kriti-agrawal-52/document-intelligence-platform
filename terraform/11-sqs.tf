# /terraform/11-sqs.tf

# Dead-Letter Queue (DLQ) for failed messages
resource "aws_sqs_queue" "summarization_dlq" {
  name = "summarization-jobs-dlq"
  tags = {
    Project = "doc-intel-app"
  }
}

# Main SQS queue for summarization jobs
resource "aws_sqs_queue" "summarization_queue" {
  name                      = "summarization-jobs-queue"
  delay_seconds             = 0
  max_message_size          = 262144 # 256 KiB
  message_retention_seconds = 345600 # 4 days
  visibility_timeout_seconds = 300 # 5 minutes, long enough for summarization

  # Link to the DLQ
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.summarization_dlq.arn
    maxReceiveCount     = 3 # After 3 failed attempts, move to DLQ
  })

  tags = {
    Project = "doc-intel-app"
  }
}
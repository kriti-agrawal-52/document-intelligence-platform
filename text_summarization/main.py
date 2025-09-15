# text_summarisation_service/main.py

import asyncio
import json
import os
from contextlib import asynccontextmanager

import boto3
import openai
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

# --- Configuration ---
MONGO_CONN_STR = os.getenv("MONGO_CONNECTION_STRING")
MONGO_DB_NAME = os.getenv("MONGO_DATABASE_NAME", "doc-intel-db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "extracted_texts")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Global Clients ---
mongo_client: AsyncIOMotorClient = None
db_collection = None
openai_client: openai.AsyncOpenAI = None
sqs_client = None


# --- Lifespan Manager for Connections ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, db_collection, openai_client, sqs_client
    print("Starting up summarization service...")

    print(f"Connecting to MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGO_CONN_STR)
    db_collection = mongo_client[MONGO_DB_NAME][MONGO_COLLECTION_NAME]
    print("MongoDB connection successful.")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")
    openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized.")

    if not SQS_QUEUE_URL:
        raise ValueError("SQS_QUEUE_URL is not set.")
    sqs_client = boto3.client("sqs", region_name=AWS_REGION)
    print(f"SQS client initialized for queue: {SQS_QUEUE_URL}")

    print("Starting SQS polling loop...")
    asyncio.create_task(poll_sqs_queue())

    yield

    print("Shutting down...")
    if mongo_client:
        mongo_client.close()


# --- FastAPI App ---
app = FastAPI(title="Text Summarization Service", version="1.0.0", lifespan=lifespan)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Summarization Service is healthy"}


# --- SQS Worker Logic ---
class SQSMessageBody(BaseModel):
    document_id: str
    user_id: int
    text_to_summarize: str


async def process_message(message: dict):
    try:
        receipt_handle = message["ReceiptHandle"]
        body_data = json.loads(message["Body"])

        validated_body = SQSMessageBody(**body_data)
        doc_id = validated_body.document_id
        text = validated_body.text_to_summarize

        print(f"Processing document ID: {doc_id}")

        prompt = f"Please provide a concise summary of the following text:\n\n{text}"
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        summary = response.choices[0].message.content.strip()

        await db_collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"summary": summary, "status": "complete"}},
        )
        print(f"Successfully summarized and updated document ID: {doc_id}")

        sqs_client.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
        print(f"Deleted message for document ID: {doc_id} from SQS.")

    except Exception as e:
        print(f"Error processing message: {e}. Message will be retried or sent to DLQ.")


async def poll_sqs_queue():
    while True:
        try:
            print("Polling for messages...")
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20,
                MessageAttributeNames=["All"],
            )

            messages = response.get("Messages", [])
            if messages:
                print(f"Received {len(messages)} messages.")
                await asyncio.gather(*(process_message(msg) for msg in messages))
            else:
                print("No messages received. Waiting...")

        except Exception as e:
            print(f"An error occurred in the polling loop: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

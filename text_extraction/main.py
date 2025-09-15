# text_extraction_service/main.py

import asyncio
import base64
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO

import boto3
import openai
from bson import ObjectId
from fastapi import (Depends, FastAPI, File, Form, HTTPException, UploadFile,
                     status)
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
# --- Import local modules ---
from text_extraction_service.database import (close_mongo_connection,
                                              connect_to_mongo,
                                              get_extracted_texts_collection)
from text_extraction_service.redis_cache import (cache_extraction,
                                                 close_redis_connection,
                                                 connect_to_redis,
                                                 get_cached_extraction)

from shared.auth_utils import get_current_user_id
from shared.config import get_config, get_env_vars
from shared.jwt_blacklist import (close_jwt_blacklist_redis,
                                  init_jwt_blacklist_redis)

# --- Global Configuration and Clients ---
config_data = get_config()
env_vars = get_env_vars()
openai_client = None
sqs_client = None
s3_client = None
# Environment variables
SQS_QUEUE_URL = env_vars.SQS_QUEUE_URL
AWS_REGION = env_vars.AWS_REGION
S3_BUCKET = env_vars.S3_USER_IMAGES_BUCKET

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Text Extraction Service",
    description="Extracts text and queues summarization jobs.",
    version="0.3.0",
    lifespan=lifespan,  # The lifespan manager is defined below
)


# --- Lifespan Manager for Connections ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global openai_client, sqs_client, s3_client

    # Initialize OpenAI client
    if not env_vars.openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    openai_client = openai.AsyncOpenAI(api_key=env_vars.openai_api_key)
    print("OpenAI client initialized.")

    # Initialize SQS client if the URL is configured
    if SQS_QUEUE_URL:
        sqs_client = boto3.client("sqs", region_name=AWS_REGION)
        print(f"SQS client initialized for queue: {SQS_QUEUE_URL}")

    # Initialize S3 client if bucket is configured
    if S3_BUCKET:
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        print(f"S3 client initialized for bucket: {S3_BUCKET}")

    # Use asyncio.gather to initialize database connections concurrently
    await asyncio.gather(
        connect_to_mongo(), connect_to_redis(), init_jwt_blacklist_redis()
    )

    print("Startup complete.")
    yield  # The application is now running

    # --- Cleanup on Shutdown ---
    print("Shutting down...")
    if openai_client:
        # The openai client uses httpx which is best closed explicitly
        await openai_client.close()
        print("OpenAI client closed.")

    await asyncio.gather(
        close_mongo_connection(), close_redis_connection(), close_jwt_blacklist_redis()
    )
    print("Shutdown complete.")


# --- Helper Functions ---
async def upload_image_to_s3(image_bytes: bytes, s3_key: str, content_type: str) -> str:
    """Upload image to S3 and return the S3 URL."""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType=content_type,
            Metadata={
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "service": "text-extraction",
            },
        )
        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"Successfully uploaded image to S3: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Failed to upload image to S3: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload image to S3: {str(e)}"
        )


async def encode_image_to_base64_url(image_bytes: bytes):
    """Encodes image bytes to a base64 data URL."""
    try:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
        }
    except Exception as e:
        print(f"Failed to encode image to base64: {e}")
        return None


async def create_openai_image_message(image_message: dict, prompt: str):
    """Creates a single OpenAI message for image processing."""
    return {
        "role": "user",
        "content": [{"type": "text", "text": prompt}, image_message],
    }


async def cache_user_recent_extractions(
    user_id: int, document_id: str, image_name: str, s3_url: str
):
    """Cache user's recent extractions in Redis for fast retrieval."""
    try:
        cache_key = config_data.cache.redis_key_patterns.user_recent_extractions.format(
            user_id=user_id
        )
        extraction_data = {
            "document_id": document_id,
            "image_name": image_name,
            "s3_url": s3_url,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        # Use Redis cache function from redis_cache.py
        await cache_extraction(
            cache_key,
            json.dumps(extraction_data),
            ttl=config_data.cache.ttl.user_recent_extractions,
        )
        print(f"Cached recent extraction for user {user_id}: {document_id}")
    except Exception as e:
        print(f"Failed to cache user recent extractions: {e}")
        # Don't fail the request if caching fails


# --- Pydantic Models for API Responses ---
class DocumentStatusResponse(BaseModel):
    document_id: str
    image_name: str
    status: str
    extracted_text: str
    summary: str | None = None
    s3_url: str | None = None
    created_at: str
    updated_at: str | None = None


class JobAcceptedResponse(BaseModel):
    message: str
    document_id: str
    image_name: str
    extracted_text: str
    s3_url: str


class DocumentMetadata(BaseModel):
    document_id: str
    image_name: str
    status: str
    created_at: str
    updated_at: str | None = None
    s3_url: str | None = None
    has_summary: bool


# --- API Endpoints ---
@app.get(
    config_data.services.text_extraction_service.base_path + "/health", tags=["Health"]
)
async def health_check():
    return {"status": "Text Extraction Service is healthy!"}


@app.post(
    config_data.services.text_extraction_service.base_path + "/image_text",
    summary="Extract text from an uploaded image and start summarization job.",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Extraction"],
)
async def extract_text_from_image(
    user_id: int = Depends(get_current_user_id),
    image: UploadFile = File(...),
    image_name: str = Form(...),
    collection: AsyncIOMotorCollection = Depends(get_extracted_texts_collection),
):
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed.",
        )

    # Check for duplicate document name for this user
    existing_doc = await collection.find_one(
        {"image_name": image_name, "user_id": user_id}
    )
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A document with the name '{image_name}' already exists.",
        )

    try:
        # Step 1: Read image bytes
        image_bytes = await image.read()

        # Step 2: Create document in DB first to get document_id
        current_time = datetime.now(timezone.utc)
        db_document = {
            "image_name": image_name,
            "user_id": user_id,
            "extracted_text": "",
            "summary": None,
            "status": "uploading",
            "s3_url": None,
            "created_at": current_time,
            "updated_at": current_time,
        }
        insert_result = await collection.insert_one(db_document)
        document_id = str(insert_result.inserted_id)

        # Step 3: Upload to S3 with format {user_id}_{document_id}_{image_name}
        file_extension = (
            image.filename.split(".")[-1] if "." in image.filename else "jpg"
        )
        s3_key = f"{user_id}_{document_id}_{image_name}.{file_extension}"
        s3_url = await upload_image_to_s3(image_bytes, s3_key, image.content_type)

        # Step 4: Update document with S3 URL
        await collection.update_one(
            {"_id": insert_result.inserted_id},
            {
                "$set": {
                    "s3_url": s3_url,
                    "status": "processing_extraction",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        # Step 5: Extract text using OpenAI
        image_message_content = await encode_image_to_base64_url(image_bytes)
        if not image_message_content:
            await collection.update_one(
                {"_id": insert_result.inserted_id},
                {
                    "$set": {
                        "status": "failed",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            raise HTTPException(
                status_code=500, detail="Failed to encode image for processing."
            )

        prompt_text = config_data.openai.prompt_for_text_extraction
        openai_message = await create_openai_image_message(
            image_message_content, prompt_text
        )

        response = await openai_client.chat.completions.create(
            model=config_data.openai.model,
            messages=[openai_message],
            max_tokens=config_data.openai.max_tokens,
            temperature=config_data.openai.temperature,
        )

        extracted_text_result = response.choices[0].message.content
        if not extracted_text_result:
            await collection.update_one(
                {"_id": insert_result.inserted_id},
                {
                    "$set": {
                        "status": "failed",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            raise HTTPException(status_code=500, detail="OpenAI returned no text.")

        # Step 6: Update document with extracted text
        await collection.update_one(
            {"_id": insert_result.inserted_id},
            {
                "$set": {
                    "extracted_text": extracted_text_result,
                    "status": "processing_summary",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        # Step 7: Send message to SQS for summarization
        if sqs_client and SQS_QUEUE_URL:
            message_body = {
                "document_id": document_id,
                "user_id": user_id,
                "text_to_summarize": extracted_text_result,
            }
            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(message_body)
            )
            print(f"Sent document ID {document_id} to SQS for summarization.")
        else:
            print("WARNING: SQS client not configured. Summarization job not queued.")
            # Mark as complete if no summarization is configured
            await collection.update_one(
                {"_id": insert_result.inserted_id},
                {
                    "$set": {
                        "status": "completed",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

        # Step 8: Cache user's recent extractions in Redis
        await cache_user_recent_extractions(user_id, document_id, image_name, s3_url)

        return JobAcceptedResponse(
            message="Text extracted successfully. Summarization is in progress.",
            document_id=document_id,
            image_name=image_name,
            extracted_text=extracted_text_result,
            s3_url=s3_url,
        )

    except openai.APIStatusError as e:
        # Update document status to failed
        if "document_id" in locals():
            await collection.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "status": "failed",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=f"OpenAI API error: {e.response.text}",
        )
    except Exception as e:
        # Update document status to failed
        if "document_id" in locals():
            await collection.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "status": "failed",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@app.get(
    config_data.services.text_extraction_service.base_path + "/documents",
    response_model=list[DocumentMetadata],
    summary="Get list of user's documents with metadata",
    tags=["Extraction"],
)
async def get_user_documents(
    user_id: int = Depends(get_current_user_id),
    collection: AsyncIOMotorCollection = Depends(get_extracted_texts_collection),
    limit: int = 50,
    skip: int = 0,
):
    """Get list of user's documents sorted by creation date (newest first)."""
    cursor = (
        collection.find({"user_id": user_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    documents = []
    async for doc in cursor:
        doc_metadata = DocumentMetadata(
            document_id=str(doc["_id"]),
            image_name=doc["image_name"],
            status=doc["status"],
            created_at=doc["created_at"].isoformat(),
            updated_at=doc.get("updated_at", doc["created_at"]).isoformat(),
            s3_url=doc.get("s3_url"),
            has_summary=bool(doc.get("summary")),
        )
        documents.append(doc_metadata)

    return documents


@app.get(
    config_data.services.text_extraction_service.base_path + "/document/{image_name}",
    response_model=DocumentStatusResponse,
    summary="Get the full details of a specific document",
    tags=["Extraction"],
)
async def get_document_status(
    image_name: str,
    user_id: int = Depends(get_current_user_id),
    collection: AsyncIOMotorCollection = Depends(get_extracted_texts_collection),
):
    document = await collection.find_one({"image_name": image_name, "user_id": user_id})
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )

    return DocumentStatusResponse(
        document_id=str(document["_id"]),
        image_name=document["image_name"],
        status=document["status"],
        extracted_text=document.get("extracted_text", ""),
        summary=document.get("summary"),
        s3_url=document.get("s3_url"),
        created_at=document["created_at"].isoformat(),
        updated_at=document.get("updated_at", document["created_at"]).isoformat(),
    )


# Run the application for local development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "text_extraction_service.main:app",
        host=config_data.services.text_extraction_service.host,
        port=config_data.services.text_extraction_service.port,
        reload=True,
    )

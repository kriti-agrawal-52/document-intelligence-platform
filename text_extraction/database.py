# text_extraction_service/database.py

import os

from motor.motor_asyncio import (AsyncIOMotorClient, AsyncIOMotorCollection,
                                 AsyncIOMotorDatabase)

from shared.config import get_config  # To get database name and credentials
from shared.config import get_env_vars

# Global MongoDB client and database/collection references
# Global MongoDB client and database/collection references
_mongo_client = None
_mongo_db = None
_extracted_texts_collection = None


async def connect_to_mongo():
    """
    Establishes connection to MongoDB and sets up global client, db, and collection references.
    Also ensures unique index for extracted texts.
    """
    global _mongo_client, _mongo_db, _extracted_texts_collection

    config = get_config()
    env_vars = get_env_vars()  # Access environment variables

    # Use env_vars for host and port
    mongo_host = env_vars.MONGODB_HOST
    mongo_port = env_vars.MONGODB_PORT
    mongo_db_name = config.databases.mongodb.extracted_text_db_name
    mongo_user = env_vars.mongodb_user
    mongo_password = env_vars.mongodb_password

    # Path to the certificate inside the Docker container
    tls_ca_file = "global-bundle.pem"

    if mongo_user and mongo_password:
        # Construct the URI without credentials for printing
        print_uri = f"mongodb://{mongo_host}:{mongo_port}/"
        # Create the client with credentials and TLS options
        _mongo_client = AsyncIOMotorClient(
            host=mongo_host,
            port=int(mongo_port),
            username=mongo_user,
            password=mongo_password,
            tls=True,
            tlsCAFile=tls_ca_file,
            retryWrites=False,  # Required for DocumentDB
        )
    else:
        # Fallback for local testing without auth
        print_uri = f"mongodb://{mongo_host}:{mongo_port}/"
        _mongo_client = AsyncIOMotorClient(host=mongo_host, port=int(mongo_port))

    print(f"Attempting to connect to MongoDB at {print_uri} for Text Extraction...")
    _mongo_db = _mongo_client[mongo_db_name]
    _extracted_texts_collection = _mongo_db[
        config.databases.mongodb.extracted_text_collection
    ]

    # Ensure unique compound index on image_name and user_id
    # This ensures a user can't save two different images with the exact same name
    try:
        await _extracted_texts_collection.create_index(
            [("image_name", 1), ("user_id", 1)],
            unique=True,
            name="unique_image_name_per_user_index",
        )
        print(
            "MongoDB unique index 'unique_image_name_per_user_index' created/checked for Text Extraction Service."
        )
    except Exception as e:
        print(f"Error creating MongoDB index for Text Extraction: {e}")
        raise

    print(
        f"Successfully connected to MongoDB database '{mongo_db_name}' and collection '{_extracted_texts_collection.name}' for Text Extraction."
    )


async def close_mongo_connection():
    """Closes the MongoDB connection."""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        print("MongoDB connection for Text Extraction closed.")


def get_extracted_texts_collection() -> AsyncIOMotorCollection:
    """Dependency to get the MongoDB extracted texts collection."""
    if _extracted_texts_collection is None:
        raise ConnectionError("MongoDB extracted texts collection not initialized.")
    return _extracted_texts_collection

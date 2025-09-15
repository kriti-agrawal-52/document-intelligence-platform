# text_extraction_service/redis_cache.py

import json

import redis.asyncio as redis

from shared.config import get_env_vars

# --- Globals for Redis Client ---
_redis_client = None


async def connect_to_redis():
    """
    Establishes a connection to the Redis cache.
    """
    global _redis_client
    env = get_env_vars()

    redis_host = env.REDIS_HOST
    redis_port = env.REDIS_PORT

    if not redis_host or not redis_port:
        print(
            "REDIS_HOST or REDIS_PORT environment variables not set. Cache is disabled."
        )
        return

    try:
        print(f"Connecting to Redis at {redis_host}:{redis_port}...")
        _redis_client = redis.Redis(
            host=redis_host, port=int(redis_port), decode_responses=True
        )
        await _redis_client.ping()
        print("Successfully connected to Redis.")
    except Exception as e:
        print(f"Could not connect to Redis: {e}")
        _redis_client = None  # Ensure client is None if connection fails


async def close_redis_connection():
    """
    Closes the Redis connection.
    """
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        print("Redis connection closed.")


def get_redis_client():
    """
    Dependency to get the Redis client.
    """
    return _redis_client


async def get_cached_extraction(user_id: int, image_name: str):
    """
    Retrieves a cached text extraction result from Redis.
    """
    if not _redis_client:
        return None

    cache_key = f"user:{user_id}:image:{image_name}"
    cached_result = await _redis_client.get(cache_key)

    if cached_result:
        print(f"Cache hit for key: {cache_key}")
        return json.loads(cached_result)

    print(f"Cache miss for key: {cache_key}")
    return None


async def cache_extraction(cache_key: str, data: str, ttl: int = 86400):
    """
    Caches data in Redis with a TTL (default 24 hours).
    This is a generic cache function that accepts any cache key and data.
    """
    if not _redis_client:
        return

    await _redis_client.set(cache_key, data, ex=ttl)
    print(f"Cached result for key: {cache_key} with TTL: {ttl}s")


async def get_cached_data(cache_key: str):
    """
    Retrieves cached data from Redis using the provided cache key.
    """
    if not _redis_client:
        return None

    cached_result = await _redis_client.get(cache_key)

    if cached_result:
        print(f"Cache hit for key: {cache_key}")
        return cached_result

    print(f"Cache miss for key: {cache_key}")
    return None


async def cache_user_recent_extractions_list(
    user_id: int, extraction_list: list, ttl: int = 86400
):
    """
    Caches a user's recent extractions list in Redis.
    """
    if not _redis_client:
        return

    cache_key = f"user:{user_id}:recent_extractions"
    await _redis_client.set(cache_key, json.dumps(extraction_list), ex=ttl)
    print(f"Cached recent extractions list for user {user_id} with TTL: {ttl}s")


async def get_user_recent_extractions_list(user_id: int):
    """
    Retrieves a user's recent extractions list from Redis cache.
    """
    if not _redis_client:
        return None

    cache_key = f"user:{user_id}:recent_extractions"
    cached_result = await _redis_client.get(cache_key)

    if cached_result:
        print(f"Cache hit for user {user_id} recent extractions")
        return json.loads(cached_result)

    print(f"Cache miss for user {user_id} recent extractions")
    return None

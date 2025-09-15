# shared/jwt_blacklist.py

from datetime import datetime, timezone
from typing import Optional

import jwt
import redis.asyncio as redis

from shared.config import get_config, get_env_vars

config = get_config()
env = get_env_vars()

# Global Redis client for JWT blacklist
_blacklist_redis_client: Optional[redis.Redis] = None


async def init_jwt_blacklist_redis():
    """Initialize Redis connection for JWT blacklist."""
    global _blacklist_redis_client

    try:
        _blacklist_redis_client = redis.Redis(
            host=env.REDIS_HOST,
            port=int(env.REDIS_PORT),
            db=int(env.REDIS_DB),
            decode_responses=True,
        )
        await _blacklist_redis_client.ping()
        print("JWT Blacklist Redis connection initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize JWT blacklist Redis: {e}")
        _blacklist_redis_client = None


async def close_jwt_blacklist_redis():
    """Close Redis connection for JWT blacklist."""
    global _blacklist_redis_client
    if _blacklist_redis_client:
        await _blacklist_redis_client.close()
        print("JWT Blacklist Redis connection closed.")


def get_token_jti(token: str) -> Optional[str]:
    """
    Extract the JTI (JWT ID) from a token without verification.
    This is used to identify tokens for blacklisting.
    """
    try:
        # Decode without verification to get the JTI
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        return unverified_payload.get("jti")
    except Exception as e:
        print(f"Failed to extract JTI from token: {e}")
        return None


def get_token_exp(token: str) -> Optional[datetime]:
    """
    Extract the expiration time from a token without verification.
    """
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = unverified_payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        return None
    except Exception as e:
        print(f"Failed to extract expiration from token: {e}")
        return None


async def blacklist_token(token: str) -> bool:
    """
    Add a JWT token to the blacklist.
    The token will be stored with TTL matching its expiration time.
    """
    if not _blacklist_redis_client:
        print("JWT Blacklist Redis not available")
        return False

    try:
        # Extract JTI and expiration from token
        jti = get_token_jti(token)
        exp_time = get_token_exp(token)

        if not jti:
            print("Token does not have JTI, cannot blacklist")
            return False

        # Calculate TTL (time until token expires)
        if exp_time:
            now = datetime.now(timezone.utc)
            ttl_seconds = int((exp_time - now).total_seconds())
            if ttl_seconds <= 0:
                print("Token already expired, no need to blacklist")
                return True
        else:
            # Fallback TTL if we can't get expiration time
            ttl_seconds = config.jwt.access_token_expire_minutes * 60

        # Store in Redis with key format: blacklist:jwt:{jti}
        blacklist_key = f"blacklist:jwt:{jti}"
        await _blacklist_redis_client.set(blacklist_key, "1", ex=ttl_seconds)

        print(f"Token {jti} blacklisted for {ttl_seconds} seconds")
        return True

    except Exception as e:
        print(f"Failed to blacklist token: {e}")
        return False


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if a JWT token is blacklisted.
    """
    if not _blacklist_redis_client:
        print("JWT Blacklist Redis not available, allowing token")
        return False

    try:
        jti = get_token_jti(token)
        if not jti:
            print("Token does not have JTI, cannot check blacklist")
            return False

        blacklist_key = f"blacklist:jwt:{jti}"
        is_blacklisted = await _blacklist_redis_client.exists(blacklist_key)

        return bool(is_blacklisted)

    except Exception as e:
        print(f"Failed to check token blacklist: {e}")
        # On error, allow the token (fail open for availability)
        return False


async def get_blacklist_stats() -> dict:
    """
    Get statistics about the JWT blacklist.
    Useful for monitoring and debugging.
    """
    if not _blacklist_redis_client:
        return {"error": "Redis not available"}

    try:
        # Count blacklisted tokens
        blacklist_keys = await _blacklist_redis_client.keys("blacklist:jwt:*")
        blacklisted_count = len(blacklist_keys)

        return {"blacklisted_tokens": blacklisted_count, "redis_connected": True}

    except Exception as e:
        return {"error": str(e), "redis_connected": False}

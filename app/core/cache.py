import redis
from app.config import settings
import json

# --- Redis Cache ---
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    redis_client = None

def set_cache(key: str, value: any, ttl: int = 3600):
    """
    Sets a value in the Redis cache.
    """
    if redis_client:
        try:
            redis_client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            print(f"Error setting cache for key '{key}': {e}")

def get_cache(key: str) -> any:
    """
    Gets a value from the Redis cache.
    """
    if redis_client:
        try:
            cached_value = redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
        except Exception as e:
            print(f"Error getting cache for key '{key}': {e}")
    return None

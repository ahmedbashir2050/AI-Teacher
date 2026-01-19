import functools
import json

import aioredis
from core.config import settings
from pydantic import BaseModel

redis = None


async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return redis


def serialize_item(obj):
    if isinstance(obj, BaseModel):
        return obj.dict() if hasattr(obj, "dict") else obj.model_dump()
    return obj


def cache_result(ttl: int = 300):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            r = await get_redis()
            # Create a cache key from args and kwargs, handling Pydantic models
            serialized_args = [serialize_item(arg) for arg in args]
            serialized_kwargs = {k: serialize_item(v) for k, v in kwargs.items()}
            key = f"{func.__name__}:{json.dumps(serialized_args, sort_keys=True)}:{json.dumps(serialized_kwargs, sort_keys=True)}"

            cached = await r.get(key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)

            # Serialize result if it contains Pydantic models
            if isinstance(result, list):
                serialized_result = [serialize_item(item) for item in result]
            else:
                serialized_result = serialize_item(result)

            await r.set(key, json.dumps(serialized_result), ex=ttl)
            return result

        return wrapper

    return decorator

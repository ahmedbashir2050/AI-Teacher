import json
import aioredis
import os
import functools
from pydantic import BaseModel

redis = None

async def get_redis():
    global redis
    if redis is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        redis = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    return redis

def serialize_item(obj):
    if isinstance(obj, BaseModel):
        return obj.dict() if hasattr(obj, 'dict') else obj.model_dump()
    return obj

def cache_result(ttl: int = 300):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            r = await get_redis()
            serialized_args = [serialize_item(arg) for arg in args]
            serialized_kwargs = {k: serialize_item(v) for k, v in kwargs.items()}
            key = f"{func.__name__}:{json.dumps(serialized_args, sort_keys=True)}:{json.dumps(serialized_kwargs, sort_keys=True)}"

            cached = await r.get(key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)

            if isinstance(result, list):
                serialized_result = [serialize_item(item) for item in result]
            else:
                serialized_result = serialize_item(result)

            await r.set(key, json.dumps(serialized_result), ex=ttl)
            return result
        return wrapper
    return decorator

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.security import decode_token


def get_username_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return token_data.username
    return None


def rate_limit_key_func(request: Request) -> str:
    """
    Key function for rate limiting.
    Prioritizes username from JWT, falls back to IP address.
    """
    username = get_username_from_request(request)
    if username:
        return username
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key_func, storage_uri=settings.REDIS_URL)

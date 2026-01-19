import httpx
from core.config import settings
from fastapi import HTTPException

class UserServiceClient:
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL

    async def get_user_by_email(self, email: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/internal/users/email/{email}")
            if resp.status_code == 404:
                return None
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="User service error")
            return resp.json()

    async def create_user(self, user_data: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/internal/users", json=user_data)
            if resp.status_code != 200:
                detail = resp.json().get("detail", "User service error")
                raise HTTPException(status_code=resp.status_code, detail=detail)
            return resp.json()

    async def update_user(self, user_id: str, update_data: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.base_url}/me",
                json=update_data,
                headers={"X-User-Id": str(user_id)}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="User service update failed")
            return resp.json()

    async def get_user_by_id(self, user_id: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/internal/users/{user_id}")
            if resp.status_code == 404:
                return None
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="User service error")
            return resp.json()

user_service_client = UserServiceClient()

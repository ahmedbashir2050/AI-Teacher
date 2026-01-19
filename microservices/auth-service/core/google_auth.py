from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
from .config import settings

def verify_google_token(token: str) -> dict:
    try:
        # Specify the GOOGLE_CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        # userid = idinfo['sub']

        # Validate issuer
        if idinfo['iss'] not in [settings.GOOGLE_ISSUER, 'accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # Check if email is verified
        if not idinfo.get('email_verified'):
            raise ValueError('Email not verified by Google.')

        return idinfo
    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

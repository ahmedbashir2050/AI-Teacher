# Authentication & Identity Management

AI Teacher uses a robust, multi-layer authentication system built for security and scalability.

## 🔑 Authentication Methods

The system supports two primary login methods:

### 1. Email & Password (Local)
Standard login using email and a hashed password (bcrypt).
- **Endpoint:** `POST /api/v1/auth/login`
- **Registration:** `POST /api/v1/auth/register`

### 2. Google Account Sign-In (OAuth 2.0)
Integrated Google login for a seamless user experience.
- **Endpoint:** `POST /api/v1/auth/google`
- **Flow:**
    1. Flutter client obtains an `id_token` using `google_sign_in`.
    2. Client sends the `id_token` to the backend.
    3. Backend verifies the token with Google public keys.
    4. Backend creates a new user or updates the existing one.
    5. Backend issues system-level JWTs.

## 🛡️ Security Architecture

### Token-Based Authentication
- **Access Token**: Short-lived JWT (30 mins) used for authorizing API requests.
- **Refresh Token**: Long-lived, rotatable token (7 days) used to obtain new access tokens.
- **Blacklisting**: Tokens can be immediately revoked (logout) using a Redis-based blacklist.

### Role-Based Access Control (RBAC)
Every user is assigned a role that determines their permissions across the system:
- `STUDENT` (Default): Access to chat, exams, and personal profile.
- `ACADEMIC`: Ability to ingest documents and manage course content.
- `ADMIN`: Full system access, including role management.

### Zero Trust Gateway
The API Gateway handles JWT verification for all protected routes. Downstream services receive trusted identity headers:
- `X-User-Id`: The UUID of the authenticated user.
- `X-User-Role`: The role of the user.

## 📝 Audit Logging

All authentication events are logged to a centralized audit system:
- `GOOGLE_LOGIN_SUCCESS`
- `GOOGLE_LOGIN_FAILURE`
- `USER_CREATED_FROM_GOOGLE`
- `login` (Local)
- `register` (Local)
- `logout`
- `refresh_token`

## ⚙️ Configuration

Required environment variables for `auth-service`:
- `GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 Client ID.
- `GOOGLE_ISSUER`: Defaults to `https://accounts.google.com`.
- `JWT_SECRET_KEY`: Secret used for signing JWTs.
- `JWT_AUDIENCE`: Expected audience claim.
- `JWT_ISSUER`: Token issuer claim.

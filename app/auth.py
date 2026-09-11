from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings


ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def create_access_token(technician_id: str) -> str:

    expires = (
        datetime.now(timezone.utc)
        + timedelta(hours=TOKEN_EXPIRE_HOURS)
    )

    payload = {
        "sub": technician_id,
        "exp": expires,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> str:

    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM]
    )

    technician_id = payload.get("sub")

    if not technician_id:
        raise ValueError("Invalid token")

    return technician_id


def get_current_technician(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:

    try:
        return decode_access_token(
            credentials.credentials
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
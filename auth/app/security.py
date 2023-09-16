from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# TODO: use asymmetric signature algorithm
jwt_signature_algorithm = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    token_data = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    token_data.update({"exp": expire})
    return jwt.encode(
        token_data,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=jwt_signature_algorithm,
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token=token,
            key=settings.jwt_secret_key.get_secret_value(),
            algorithms=[jwt_signature_algorithm],
        )
    except JWTError:
        return None

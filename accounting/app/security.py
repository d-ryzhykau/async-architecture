from typing import Optional

from jose import JWTError, jwt

from .settings import settings

jwt_signature_algorithm = "HS256"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token=token,
            key=settings.jwt_secret_key.get_secret_value(),
            algorithms=[jwt_signature_algorithm],
        )
    except JWTError:
        return None

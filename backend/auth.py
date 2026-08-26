import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Header, HTTPException, status

from backend.config import settings


def _token_expiry_minutes() -> int:
    return getattr(settings, "auth_token_ttl_minutes", 60 * 24)


def create_token(username: str) -> str:
    expiry = int((datetime.utcnow() + timedelta(minutes=_token_expiry_minutes())).timestamp())
    payload = f"{username}:{expiry}"
    signature = hmac.new(settings.secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{username}.{expiry}.{signature}"


def verify_token(token: str) -> Optional[str]:
    if not token:
        return None

    try:
        username, expiry_raw, signature = token.split(".")
        expiry = int(expiry_raw)
    except ValueError:
        return None

    if datetime.utcnow().timestamp() > expiry:
        return None

    expected = hmac.new(
        settings.secret_key.encode("utf-8"),
        f"{username}:{expiry}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return None

    return username


async def require_auth(authorization: Optional[str] = Header(default=None, alias="Authorization")) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de autenticação obrigatório")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Formato do token inválido")

    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    return username

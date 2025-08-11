import jwt
from typing import Optional


SECRET = "demo-secret"


def verify_token(token: str) -> bool:
    if not token:
        return False
    try:
        jwt.decode(token, SECRET, algorithms=["HS256"])  # nosec - demo only
        return True
    except Exception:
        return False
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(cred.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return user


def require_role(*role_codes: str):
    """Dependency that checks the current user has one of the allowed role codes."""
    async def checker(user: User = Depends(get_current_user)) -> User:
        user_codes = {r.code for r in user.roles}
        if not user_codes.intersection(role_codes):
            raise HTTPException(403, "Permission denied")
        return user
    return checker

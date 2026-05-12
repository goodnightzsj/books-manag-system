from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def _user_from_token(token: str | None, db: Session) -> User:
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    return _user_from_token(credentials.credentials, db)


def get_current_user_lenient(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Like ``get_current_user`` but also accepts the token as a ``?token=``
    query parameter. Needed for media endpoints (``/files/stream`` etc.) whose
    URLs are handed to ``<img>`` / pdf.js / epub.js, which cannot set an
    ``Authorization`` header."""
    raw = (credentials.credentials if credentials else None) or token
    return _user_from_token(raw, db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

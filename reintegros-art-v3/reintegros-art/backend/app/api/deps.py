"""
Dependencias de FastAPI: extracción del usuario actual desde JWT,
y guards de permisos por acción.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.core.security import decode_token
from app.core.constants import tiene_permiso


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise cred_exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise cred_exc
    if not user.activo or user.bloqueado:
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")
    return user


def require_permission(accion: str):
    """Factory de dependency que valida un permiso."""
    def _checker(user: User = Depends(get_current_user)) -> User:
        if not tiene_permiso(user.role, accion):
            raise HTTPException(
                status_code=403,
                detail=f"Sin permiso para: {accion}",
            )
        return user
    return _checker

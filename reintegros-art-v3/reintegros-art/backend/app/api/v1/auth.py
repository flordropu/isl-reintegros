"""Endpoints de autenticación."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.user import LoginRequest, TokenResponse, UserOut
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user
from app.services.reintegro_service import registrar_audit


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not user.activo or user.bloqueado:
        raise HTTPException(status_code=403, detail="Usuario inactivo o bloqueado")

    user.ultimo_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, extra_claims={"role": user.role.value})
    registrar_audit(db, usuario_id=user.id, accion="auth.login", descripcion=f"Login exitoso: {user.email}")

    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

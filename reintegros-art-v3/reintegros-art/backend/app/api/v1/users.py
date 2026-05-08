"""ABM de usuarios."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.security import hash_password
from app.api.deps import require_permission, get_current_user
from app.core.constants import UserRole, tiene_permiso
from app.services.reintegro_service import registrar_audit


router = APIRouter(prefix="/users", tags=["Usuarios"])


def _es_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


@router.get("", response_model=list[UserOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    if not (_es_admin(actual) or tiene_permiso(actual.role, "users:read")):
        raise HTTPException(status_code=403, detail="Sin permiso")
    return db.query(User).order_by(User.creado_en.desc()).all()


@router.post("", response_model=UserOut, status_code=201)
def crear_usuario(
    data: UserCreate,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    if not _es_admin(actual):
        raise HTTPException(status_code=403, detail="Solo admin puede crear usuarios")

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")

    user = User(
        email=data.email,
        nombre_completo=data.nombre_completo,
        hashed_password=hash_password(data.password),
        role=data.role,
        region=data.region,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    registrar_audit(db, usuario_id=actual.id, accion="user.create", descripcion=f"Alta de usuario {user.email}")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def actualizar_usuario(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    if not _es_admin(actual) and actual.id != user_id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cambios = data.model_dump(exclude_unset=True)
    if "password" in cambios:
        cambios["hashed_password"] = hash_password(cambios.pop("password"))
    # solo admin puede cambiar role / activo / bloqueado
    if not _es_admin(actual):
        for k in ("role", "activo", "bloqueado"):
            cambios.pop(k, None)

    for k, v in cambios.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    registrar_audit(db, usuario_id=actual.id, accion="user.update", descripcion=f"Modificación usuario {user.email}")
    return user


@router.delete("/{user_id}", status_code=204)
def desactivar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    """Soft delete: marca como inactivo."""
    if not _es_admin(actual):
        raise HTTPException(status_code=403, detail="Solo admin puede desactivar usuarios")
    if user_id == actual.id:
        raise HTTPException(status_code=400, detail="No podés desactivarte a vos mismo")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.activo = False
    db.commit()
    registrar_audit(db, usuario_id=actual.id, accion="user.deactivate", descripcion=f"Baja usuario {user.email}")

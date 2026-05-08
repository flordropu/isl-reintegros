"""
Configuración de base de datos: engine, session factory y Base declarativa.
"""
import unicodedata
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings


connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)


# Para SQLite: registramos una función `unaccent` que strippea acentos.
# Permite búsquedas accent-insensitive vía sa_func.lower() + LIKE sobre la
# columna ya normalizada cuando convenga.
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_conn, _):
        def unaccent(s):
            if s is None:
                return None
            return ''.join(
                c for c in unicodedata.normalize('NFD', str(s))
                if unicodedata.category(c) != 'Mn'
            )
        dbapi_conn.create_function("unaccent", 1, unaccent)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Dependency de FastAPI para inyectar sesión de DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

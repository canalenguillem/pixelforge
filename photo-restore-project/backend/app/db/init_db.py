"""Inicialización de la base de datos.

Placeholder inicial: creará las tablas a partir del metadata de los modelos.
No se ejecuta nada todavía.
"""

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """Crea las tablas (idempotente). Placeholder — sin datos semilla aún."""
    # NOTA: en producción se usará Alembic para migraciones en lugar de esto.
    Base.metadata.create_all(bind=engine)

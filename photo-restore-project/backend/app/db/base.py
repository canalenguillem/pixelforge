"""Declarative Base de SQLAlchemy.

Todos los modelos ORM heredan de `Base`. Importar los modelos aquí (o en
init_db) asegura que queden registrados en el metadata.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""

    pass

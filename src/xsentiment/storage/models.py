"""Project-specific declarative metadata; domain models will follow canonical contracts."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base for this repository's own models (not copied from GraphOne)."""

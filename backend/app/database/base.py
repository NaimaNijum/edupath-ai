from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.database.models import entities  # noqa: E402,F401

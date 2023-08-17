import enum
import uuid

from sqlalchemy import UUID, Boolean, Enum, Index, String
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    manager = "manager"
    accountant = "accountant"
    worker = "worker"


# TODO: use type hints for column definitions
class User(Base):
    __tablename__ = "user"

    # TODO: use separate internal and public ID's
    uuid = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email = mapped_column(String(256), nullable=False, unique=True)
    role = mapped_column(
        Enum(UserRole, create_constraint=True, native_enum=False),
        nullable=False,
    )
    password_hash = mapped_column(String, nullable=False)
    is_deleted = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index(
            "key_email_not_is_deleted",
            "email",
            unique=True,
            postgresql_where=~is_deleted,
        ),
    )

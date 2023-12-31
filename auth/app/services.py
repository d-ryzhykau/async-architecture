from typing import List, Optional

from psycopg2.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .db import Session
from .event_producer import UserCreatedV1, UserDeletedV1, UserUpdatedV1, send_events
from .models import User
from .security import get_password_hash, verify_password


class UserEmailAlreadyUsed(Exception):
    """Raised on User.email unique constraint violation."""


class UserNotFound(Exception):
    """Raised when a User was not found."""


class UserPasswordVerificationFailed(Exception):
    """Raised on User password verification failure."""


# TODO: rework to guarantee that kafka message is dispatched for each DB write
class UserService:
    def __init__(self, session: Session):
        self.session = session
        # TODO: get event_producer

    def _get_active_users_query(self):
        """Returns a query of non-deleted Users."""
        return select(User).filter_by(is_deleted=False)

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticates a User by `email` and `password`.

        Returns:
            Authenticated `User` or None if authentication failed.
        """
        query = self._get_active_users_query().filter_by(email=email)
        user = self.session.scalars(query).one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def get_users(self) -> List[User]:
        query = self._get_active_users_query()
        return self.session.scalars(query).all()

    def get_user_by_id(self, id_: int) -> Optional[User]:
        query = self._get_active_users_query().filter_by(id=id_)
        return self.session.scalars(query).one_or_none()

    def create_user(self, email: str, password: str, role: str) -> User:
        """Create a new User.

        Returns:
            Created `User`.

        Raises:
            `UserEmailAlreadyUsed`: when a User with given email already
                exists.
        """
        user = User(
            email=email,
            role=role,
            password_hash=get_password_hash(password),
        )

        with self.session.begin():
            self.session.add(user)
            try:
                self.session.flush()
            except IntegrityError as exc:
                if isinstance(exc.orig, UniqueViolation) and (
                    exc.orig.diag.constraint_name == "key_email_not_is_deleted"
                ):
                    raise UserEmailAlreadyUsed from exc
                raise

            self.session.refresh(user)

            send_events([UserCreatedV1.from_user(user)])

        return user

    def update_user(self, id_: int, new_email: str) -> User:
        """Update an existing User.

        Returns:
            Updated `User`.

        Raises:
            `UserEmailAlreadyUsed`: when a User with given email already
                exists.
            `UserNotFound`: when a User with given UUID was not found.
        """
        with self.session.begin():
            user = self.get_user_by_id(id_)

            user.email = new_email
            try:
                self.session.flush()
            except IntegrityError as exc:
                if isinstance(exc.orig, UniqueViolation) and (
                    exc.orig.diag.constraint_name == "key_email_not_is_deleted"
                ):
                    raise UserEmailAlreadyUsed from exc
                raise

            self.session.refresh(user)

            send_events([UserUpdatedV1.from_user(user)])

        return user

    def delete_user(self, id_: int):
        """Soft-delete User with given UUID.

        Raises:
            `UserNotFound`: when a User with given UUID was not found.
        """
        with self.session.begin():
            user = self.get_user_by_id(id_)
            if user is None:
                raise UserNotFound

            user.is_deleted = True
            self.session.flush()

            self.session.refresh(user)

            send_events([UserDeletedV1.from_user(user)])

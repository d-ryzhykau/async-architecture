from typing import Tuple

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    @classmethod
    def normalize_email(cls, email: str) -> str:
        return super().normalize_email(email).lower()

    def create_superuser(self, *args, **kwargs):
        raise NotImplementedError("You cannot create superusers in this service.")

    @classmethod
    def make_unusable_password(cls) -> str:
        return make_password(None)

    def get_or_create_user(
        self,
        public_id: str,
        email: str,
        role: str,
    ) -> Tuple["User", bool]:
        """Finds existing user by `public_id` or creates a new one with given attributes.

        Returns: 2-tuple (user, created)
            user: found or created User object
            created: boolean specifying whether a new user was created.
        """
        if not public_id:
            raise ValueError("public_id cannot be empty")
        if not email:
            raise ValueError("email cannot be empty")
        if not role:
            raise ValueError("role cannot be empty")

        return self.get_or_create(
            public_id=public_id,
            defaults={
                "email": self.normalize_email(email),
                "role": role,
                "password": self.make_unusable_password(),
            },
        )

    def update_or_create_user(
        self,
        public_id: str,
        email: str,
        role: str,
    ) -> Tuple["User", bool]:
        """Updates existing User with `public_id` or creates a new one with given attributes.

        Returns: 2-tuple (user, created)
            user: found or created User object
            created: boolean specifying whether a new user was created.
        """
        if not public_id:
            raise ValueError("public_id cannot be empty")
        if not email:
            raise ValueError("email cannot be empty")
        if not role:
            raise ValueError("role cannot be empty")

        return self.update_or_create(
            public_id=public_id,
            defaults={
                "email": self.normalize_email(email),
                "role": role,
                "password": self.make_unusable_password(),
            },
        )

    def delete_user(self, public_id: str) -> int:
        """Deletes a User with given `public_id`.

        Returns:
            number of deleted User records.
        """
        return self.filter(public_id=public_id, is_deleted=False).update(is_deleted=True)


class User(AbstractBaseUser):
    USERNAME_FIELD = "email"

    objects = UserManager()

    public_id = models.UUIDField(unique=True)

    email = models.EmailField(_("email address"))
    role = models.CharField(max_length=16)
    is_deleted = models.BooleanField(default=False)

    # for django.contrib.auth compatibility
    @property
    def is_active(self) -> bool:
        return not self.is_deleted

    class Meta:
        db_table = "user"

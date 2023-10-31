import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    @classmethod
    def normalize_email(self, email: str) -> str:
        return super().normalize_email(email).lower()

    def create_user(
        self,
        email: str,
        role: str,
    ) -> "User":
        if not email:
            raise ValueError("email cannot be empty")
        if not role:
            raise ValueError("role cannot be empty")

        user = self.model(email=self.normalize_email(email), role=role)
        user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, *_, **__):
        raise NotImplementedError(
            "You cannot create superusers in this service."
        )


class User(AbstractBaseUser):
    USERNAME_FIELD = "email"

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

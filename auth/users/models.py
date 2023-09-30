import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    # used by django.contrib.auth.backends.ModelBackend
    def get_by_natural_key(self, username) -> "User":
        return self.get(**{self.model.USERNAME_FIELD: username, "is_deleted": False})

    def create_user(
        self,
        email: str,
        role: str,
        password: str,
        **extra_fields,
    ) -> "User":
        if not email:
            raise ValueError("email cannot be empty")
        if not role:
            raise ValueError("role cannot be empty")
        if not password:
            raise ValueError("password cannot be empty")

        user = self.model(
            email=self.normalize_email(email.lower()),
            role=role,
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields) -> "User":
        return self.create_user(
            email=email,
            password=password,
            role=User.Role.ADMIN,
            is_superuser=True,
        )


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "email"

    objects = UserManager()

    class Role(models.TextChoices):
        WORKER = "worker", _("Worker")
        MANAGER = "manager", _("Manager")
        ACCOUNTANT = "accountant", _("Accountant")
        ADMIN = "admin", _("Admin")

    public_id = models.UUIDField(unique=True, default=uuid.uuid4)

    email = models.EmailField(_("email address"))
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.WORKER)
    is_deleted = models.BooleanField(default=False)

    # for django.contrib.auth compatibility
    @property
    def is_active(self) -> bool:
        return not self.is_deleted

    # for django.contrib.admin compatibility
    @property
    def is_staff(self) -> bool:
        return self.role == self.Role.ADMIN

    class Meta:
        db_table = "user"
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(is_deleted=False),
                name="user_email_is_deleted_false_key",
            ),
        ]

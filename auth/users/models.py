import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, role, password, **extra_fields):
        if not email:
            raise ValueError("email cannot be empty")
        user = self.model(
            email=self.normalize_email(email.lower()),
            role=role,
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    objects = UserManager()

    class Role(models.TextChoices):
        WORKER = "worker", _("Worker")
        MANAGER = "manager", _("Manager")
        ACCOUNTANT = "accountant", _("Accountant")
        ADMIN = "admin", _("Admin")

    public_id = models.UUIDField(unique=True, default=uuid.uuid4)

    username = None  # stub inherited username field
    email = models.EmailField(_("email address"), unique=True)

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.WORKER)

    class Meta:
        db_table = "user"

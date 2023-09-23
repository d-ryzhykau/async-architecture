from .models import User


def user_create(email: str, role: str, password: str) -> User:
    return User.objects.create_user(email=email, role=role, password=password)


def user_create_superuser(email: str, role: str, password: str) -> User:
    return User.objects.create_superuser(email=email, role=role, password=password)

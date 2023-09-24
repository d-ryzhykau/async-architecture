from .models import User


def user_create(
    email: str,
    role: str,
    password: str,
    is_staff: bool = False,
    is_superuser: bool = False,
) -> User:
    user = User.objects.create_user(
        email=email,
        role=role,
        password=password,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    # TODO: send CUD event
    return user

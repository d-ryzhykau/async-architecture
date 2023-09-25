from typing import Optional

from .models import User


def user_create(email: str, role: str, password: str) -> User:
    user = User.objects.create_user(
        email=email,
        role=role,
        password=password,
    )
    # TODO: send CUD event
    return user


def user_update(
    user: User,
    email: Optional[str] = None,
    role: Optional[str] = None,
):
    update_fields = []
    if email:
        user.email = email
        update_fields.append("email")
    if role:
        user.role = role
        update_fields.append("role")
        # TODO: send business event
    user.save(update_fields=update_fields)
    # TODO: send CUD event


def user_delete(user: User):
    user.is_deleted = False
    user.save(update_fields=["is_deleted"])
    # TODO: send CUD event

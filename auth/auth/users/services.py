from typing import Optional

from django.db import transaction

from .models import User
from auth.outbox.services import event_create

USERS_STREAM_TOPIC = "users-stream"


@transaction.atomic
def user_create(
    email: str,
    role: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    user = User.objects.create_user(
        email=email,
        role=role,
        password=password,
        is_superuser=is_superuser,
    )

    public_id_str = str(user.public_id)
    event_create(
        topic=USERS_STREAM_TOPIC,
        name="User.created",
        version=1,
        key=public_id_str,
        data={
            "public_id": public_id_str,
            "email": user.email,
            "role": user.role,
        },
    )

    return user


@transaction.atomic
def user_update(
    user: User,
    email: Optional[str] = None,
    is_superuser: Optional[bool] = None,
) -> User:
    update_fields = []

    if email is not None:
        email = User.objects.normalize_email(email)
        if email != user.email:
            user.email = email
            update_fields.append("email")

    if is_superuser is not None:
        if is_superuser != user.is_superuser:
            user.is_superuser = is_superuser
            update_fields.append("is_superuser")

    user.save(update_fields=update_fields)

    if "email" in update_fields:
        public_id_str = str(user.public_id)
        event_create(
            topic=USERS_STREAM_TOPIC,
            name="User.updated",
            version=1,
            key=public_id_str,
            data={
                "public_id": public_id_str,
                "email": user.email,
                "role": user.role,
            },
        )

    return user


@transaction.atomic
def user_delete(user: User):
    user.is_deleted = True
    user.save(update_fields=["is_deleted"])

    public_id_str = str(user.public_id)
    event_create(
        topic=USERS_STREAM_TOPIC,
        name="User.deleted",
        version=1,
        key=public_id_str,
        data={"public_id": public_id_str},
    )

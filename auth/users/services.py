from django.db import transaction

from .models import User
from outbox.services import event_create

USERS_STREAM_TOPIC = "users-stream"


@transaction.atomic
def user_create(email: str, role: str, password: str) -> User:
    user = User.objects.create_user(
        email=email,
        role=role,
        password=password,
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
    email: str,
) -> User:
    email = User.objects.normalize_email(email)
    if email == user.email:
        return user

    user.email = email
    user.save(update_fields=["email"])

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

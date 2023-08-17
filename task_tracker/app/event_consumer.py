import logging
import sys

from kafka import KafkaConsumer
from pydantic import BaseModel, ValidationError
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert

from .db import Session
from .models import User
from .settings import settings

logger = logging.getLogger(__name__)


def user_created_handler(data: dict):
    with Session() as session:
        with session.begin():
            session.execute(
                insert(User)
                .values(
                    public_id=data["public_id"],
                    email=data["email"],
                    role=data["role"],
                )
                .on_conflict_do_nothing()
            )
    logger.debug("Created User %s", data["public_id"])


def user_updated_handler(data: dict):
    with Session() as session:
        with session.begin():
            session.execute(
                update(User)
                .filter_by(public_id=data["public_id"])
                .values(
                    email=data["email"],
                    role=data["role"],
                )
            )
    logger.debug("Updated User %s", data["public_id"])


def user_deleted_handler(data: dict):
    with Session() as session:
        with session.begin():
            session.execute(
                delete(User)
                .filter_by(public_id=data["public_id"])
            )
    logger.debug("Deleted User %s", data["public_id"])


EVENT_HANDLERS = {
    "UserCreated": user_created_handler,
    "UserUpdated": user_updated_handler,
    "UserDeleted": user_deleted_handler,
}


class Event(BaseModel):
    event_name: str
    data: dict


def main():
    consumer = KafkaConsumer(
        bootstrap_servers=settings.kafka_address,
        group_id="task_tracker",
        auto_offset_reset="earliest",
    )
    consumer.subscribe("auth.cud.user.0")

    logger.info("Consumer initialized. Start consuming messages...")

    for message in consumer:
        message_id = f"{message.topic}:{message.partition}:{message.offset}"
        if message.value is None:
            logger.debug(
                "Skipping message with no value: %s",
                message_id,
            )
            continue

        try:
            event = Event.model_validate_json(message.value)
        except ValidationError:
            logger.exception("Message value has invalid format: %s", message_id)
            continue

        handler = EVENT_HANDLERS.get(event.event_name)
        if not handler:
            logger.debug(
                "Unknown event name: %r, message: %s",
                event.event_name,
                message_id,
            )
            continue

        try:
            handler(event.data)
        except Exception:
            logger.exception("Failed processing event: %s", message_id)


if __name__ == "__main__":
    logging.basicConfig()

    logging_level = logging.DEBUG if "-v" in sys.argv else logging.INFO
    logger.setLevel(logging_level)

    main()

import logging
import sys
from decimal import Decimal

from kafka import KafkaConsumer
from pydantic import BaseModel, ValidationError
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from .db import Session
from .models import User, Task, AuditLogRecordReason
from .settings import settings
from .services import AccountingService

logger = logging.getLogger(__name__)


def user_created_v1_handler(data: dict):
    with Session() as session:
        accounting_service = AccountingService(session)
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
            accounting_service.create_account(data["public_id"])
    logger.debug("Created User %s", data["public_id"])


def user_updated_v1_handler(data: dict):
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


def user_deleted_v1_handler(data: dict):
    with Session() as session:
        with session.begin():
            session.execute(
                update(User)
                .filter_by(public_id=data["public_id"])
                .values(is_deleted=True)
            )
    logger.debug("Deleted User %s", data["public_id"])


def task_created_v1_handler(data: dict):
    with Session() as session:
        with session.begin():
            session.execute(
                insert(Task)
                .values(
                    public_id=data["public_id"],
                    description=data["description"],
                    jira_id=data["jira_id"],
                    assignment_price=data["assignment_price"],
                    completion_price=data["completion_price"],
                )
            )
    logger.debug("Created Task %s", data["public_id"])


# TODO: add only-once processing guarantees to avoid wrongful balance changes
def new_task_added_v1_handler(data: dict):
    with Session() as session:
        accounting_service = AccountingService(session)
        accounting_service.credit_account(
            owner_public_id=data["assigned_to_public_id"],
            amount=Decimal(data["assignment_price"]),
            reason=AuditLogRecordReason.task_assigned,
            info={"task_public_id": data["public_id"]},
        )
    logger.debug("Processed assignment of new Task %s", data["public_id"])


# TODO: add only-once processing guarantees to avoid wrongful balance changes
def task_reassigned_v1_handler(data: dict):
    with Session() as session:
        accounting_service = AccountingService(session)
        accounting_service.credit_account(
            owner_public_id=data["assigned_to_public_id"],
            amount=Decimal(data["assignment_price"]),
            reason=AuditLogRecordReason.task_assigned,
            info={"task_public_id": data["public_id"]},
        )
    logger.debug("Processed reassignment of Task %s", data["public_id"])


# TODO: add only-once processing guarantees to avoid wrongful balance changes
def task_completed_v1_handler(data: dict):
    with Session() as session:
        accounting_service = AccountingService(session)
        accounting_service.debit_account(
            owner_public_id=data["assigned_to_public_id"],
            amount=Decimal(data["completion_price"]),
            reason=AuditLogRecordReason.task_completed,
            info={"task_public_id": data["public_id"]},
        )
    logger.debug("Processed completion of Task %s", data["public_id"])


EVENT_HANDLERS = {
    # auth
    ("User.created", 1): user_created_v1_handler,
    ("User.updated", 1): user_updated_v1_handler,
    ("User.deleted", 1): user_deleted_v1_handler,
    # task_tracker
    ("Task.created", 1): task_created_v1_handler,
    ("NewTaskAdded", 1): new_task_added_v1_handler,
    ("TaskReassigned", 1): task_reassigned_v1_handler,
    ("TaskCompleted", 1): task_completed_v1_handler,
}


class Event(BaseModel):
    event_name: str
    event_version: int
    data: dict


def main():
    consumer = KafkaConsumer(
        bootstrap_servers=settings.kafka_address,
        group_id="accounting",
        auto_offset_reset="earliest",
    )
    consumer.subscribe(["users-stream", "tasks-stream", "tasks-lifecycle"])

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
            # TODO: dead-letter queue
            logger.exception("Message value has invalid format: %s", message_id)
            continue

        handler = EVENT_HANDLERS.get((event.event_name, event.event_version))
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
            # TODO: dead-letter queue
            logger.exception("Failed processing event: %s", message_id)


if __name__ == "__main__":
    logging.basicConfig()

    logging_level = logging.DEBUG if "-v" in sys.argv else logging.INFO
    logger.setLevel(logging_level)

    main()

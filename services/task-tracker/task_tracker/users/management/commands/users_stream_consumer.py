import json
import logging
from typing import TypedDict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from kafka import KafkaConsumer

from task_tracker.users.models import User

logger = logging.LoggerAdapter(logging.getLogger("users_stream_consumer"))


class UserCreatedData(TypedDict):
    public_id: str
    email: str
    role: str


class UserUpdatedData(TypedDict):
    public_id: str
    email: str
    role: str


class UserDeletedData(TypedDict):
    public_id: str


class Command(BaseCommand):
    def process_user_created(self, data: UserCreatedData):
        public_id = data["public_id"]
        user, created = User.objects.get_or_create_user(
            public_id=public_id,
            email=data["email"],
            role=data["role"],
        )
        if created:
            logger.info("User created. public_id=%s", public_id)
        else:
            logger.warning("User already exists. public_id=%s", public_id)

    def process_user_updated(self, data: UserUpdatedData):
        public_id = data["public_id"]
        user, created = User.objects.update_or_create_user(
            public_id=public_id,
            email=data["email"],
            role=data["role"],
        )
        if created:
            logger.warning(
                "Updated User did not exist. public_id=%s",
                public_id,
            )
        else:
            logger.info("User updated. public_id=%s", public_id)

    def process_user_deleted(self, data: UserDeletedData):
        public_id = data["public_id"]
        deleted_users_count = User.objects.delete_user(public_id=public_id)
        if deleted_users_count == 1:
            logger.info("User deleted. public_id=%s", public_id)
        else:
            logger.warning("Deleted User was not found. public_id=%s", public_id)

    def handle(self, *args, **options):
        # mapping of (event_name, event_version) tuple to a processor method
        routes = {
            ("User.created", 1): self.process_user_created,
            ("User.updated", 1): self.process_user_updated,
            ("User.deleted", 1): self.process_user_deleted,
        }

        consumer = KafkaConsumer(
            settings.KAFKA_USERS_STREAM_TOPIC,
            bootstrap_servers=settings.KAFKA_ADDRESS,
            group_id=settings.KAFKA_CONSUMER_GROUP_ID,
            auto_offset_reset="earliest",
        )

        for message in consumer:
            logger.extra = {
                "message_topic": message.topic,
                "message_partition": message.partition,
                "message_offset": message.offset,
                "message_key": message.key,
                "message_value": message.value,
            }

            try:
                payload = json.loads(message.value)
            except json.JSONDecodeError:
                logger.error(
                    "Could not parse message as JSON. "
                    "topic=%s partition=%s offset=%s key=%s value=%s",
                    message.topic, message.partition, message.offset, message.key, message.value,
                )
                continue

            try:
                event_name = payload["event_name"]
                event_version = payload["event_version"]
                data = payload["data"]
            except (TypeError, KeyError):
                logger.error(
                    "Invalid format of message payload. "
                    "topic=%s partition=%s offset=%s key=%s value=%s",
                    message.topic, message.partition, message.offset, message.key, message.value,
                )
                continue

            logger.extra.update(
                {
                    "event_name": event_name,
                    "event_version": event_version,
                }
            )

            processor = routes.get((event_name, event_version))
            if not processor:
                logger.warning(
                    "Unknown event: event_name=%s event_version=%s. "
                    "topic=%s partition=%s offset=%s key=%s value=%s",
                    event_name, event_version,
                    message.topic, message.partition, message.offset, message.key, message.value,
                )
                continue

            try:
                processor(data)
            except Exception:
                logger.exception(
                    "Error during event processing. "
                    "topic=%s partition=%s offset=%s key=%s value=%s",
                    message.topic, message.partition, message.offset, message.key, message.value,
                )

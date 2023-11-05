import json
from typing import Any

from event_schema_registry import EventSchemaRegistry
from django.conf import settings
from kafka import KafkaProducer

from .utils import ThreadSafeLazyObject


event_schema_registry = EventSchemaRegistry()


def key_serializer(key: str) -> bytes:
    return key.encode()


def value_serializer(value) -> bytes:
    return json.dumps(value).encode()


def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_ADDRESS,
        key_serializer=key_serializer,
        value_serializer=value_serializer,
    )


kafka_producer = ThreadSafeLazyObject(get_kafka_producer)


def send_event(
    topic: str,
    event_name: str,
    event_version: int,
    key: str,
    data: Any,
):
    """Validate event against schema registry and store it."""
    event_schema_registry.validate(
        topic=topic,
        event_name=event_name,
        event_version=event_version,
        data=data,
    )
    kafka_producer.send(
        topic=topic,
        key=key,
        value={
            "event_name": event_name,
            "event_version": event_version,
            "data": data,
        }
    )

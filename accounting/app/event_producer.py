import json
from dataclasses import dataclass
from typing import ClassVar, List, Optional

from event_schema_registry import EventSchemaRegistry
from kafka import KafkaProducer

from .settings import settings
from .models import Account


def key_serializer(key):
    return key.encode()


def value_serializer(value):
    return json.dumps(value).encode()


# TODO: don't initialize on import time
producer = KafkaProducer(
    bootstrap_servers=settings.kafka_address,
    key_serializer=key_serializer,
    value_serializer=value_serializer,
)
event_schema_registry = EventSchemaRegistry()


def send_events(events: List["BaseEvent"]):
    events_data = [event.get_event_data() for event in events]
    for event, event_data in zip(events, events_data):
        # TODO: accumulate and display all errors
        event_schema_registry.validate(
            topic=event.topic,
            event_name=event.event_name,
            event_version=event.event_version,
            event=event_data,
        )
    for event, event_data in zip(events, events_data):
        producer.send(
            topic=event.topic,
            key=event.key,
            value=event_data,
        )
    producer.flush()


@dataclass
class BaseEvent:
    topic: ClassVar[str]
    event_name: ClassVar[str]
    event_version: ClassVar[int]
    key: str
    data: Optional[dict]

    # TODO: better method name
    def get_event_data(self) -> dict:
        return {
            "event_name": self.event_name,
            "event_version": self.event_version,
            "data": self.data,
        }


@dataclass
class BaseAccountStreamEvent(BaseEvent):
    topic = "accounts-stream"

    @classmethod
    def from_account(cls, account: Account):
        public_id = str(account.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "owner_public_id": str(account.owner_public_id),
                "balance": str(account.balance),
            },
        )


@dataclass
class AccountCreatedV1(BaseAccountStreamEvent):
    event_name = "Account.updated"
    event_version = 1


@dataclass
class AccountUpdatedV1(BaseAccountStreamEvent):
    event_name = "Account.updated"
    event_version = 1

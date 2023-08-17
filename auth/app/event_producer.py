import json
from dataclasses import dataclass
from typing import ClassVar, List, Optional

from kafka import KafkaProducer

from .models import User
from .settings import settings


# TODO: don't initialize on import time
producer = KafkaProducer(bootstrap_servers=settings.kafka_address)


def send_events(events: List["BaseEvent"]):
    for event in events:
        producer.send(
            topic=event.topic,
            key=event.key.encode(),
            value=event.to_json().encode(),
        )
    producer.flush()


@dataclass
class BaseEvent:
    topic: ClassVar[str]
    event_name: ClassVar[str]
    key: str
    data: Optional[dict]

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_name": self.event_name,
                "data": self.data,
            }
        )


@dataclass
class NewUserAdded(BaseEvent):
    topic = "users-lifecycle"
    event_name = "NewUserAdded"

    @classmethod
    def from_user(cls, user: User):
        public_id = str(user.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "role": user.role.value,
            },
        )


@dataclass
class BaseUserStreamEvent(BaseEvent):
    topic = "users-stream"

    @classmethod
    def from_user(cls, user: User):
        public_id = str(user.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "email": user.email,
                "role": user.role.value,
            }
        )


@dataclass
class UserCreated(BaseUserStreamEvent):
    event_name = "User.created"


@dataclass
class UserUpdated(BaseUserStreamEvent):
    event_name = "User.updated"


@dataclass
class UserDeleted(BaseUserStreamEvent):
    event_name = "User.deleted"

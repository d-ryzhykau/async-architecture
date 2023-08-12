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
class BaseUserCUDEvent(BaseEvent):
    topic = "auth.cud.user.0"

    @classmethod
    def from_user(cls, user: User):
        uuid_str = str(user.uuid)
        return cls(
            key=uuid_str,
            data={
                "uuid": uuid_str,
                "email": user.email,
                "role": user.role.value,
            }
        )


@dataclass
class UserCreated(BaseUserCUDEvent):
    event_name = "UserCreated"


@dataclass
class UserUpdated(BaseUserCUDEvent):
    event_name = "UserUpdated"


@dataclass
class UserDeleted(BaseUserCUDEvent):
    event_name = "UserDeleted"

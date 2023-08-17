import json
from dataclasses import dataclass
from typing import ClassVar, List, Optional

from kafka import KafkaProducer

from .models import Task
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
class BaseTaskBusinessEvent(BaseEvent):
    topic = "task_tracker.business.task.0"


@dataclass
class NewTaskAdded(BaseTaskBusinessEvent):
    event_name = "NewTaskAdded"

    @classmethod
    def from_task(cls, task: Task):
        public_id = str(task.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "assigned_to_public_id": str(task.assigned_to_public_id),
                "assignment_price": str(task.assignment_price),
                "completion_price": str(task.completion_price),
            },
        )


@dataclass
class TaskAssigned(BaseTaskBusinessEvent):
    event_name = "TaskAssigned"

    @classmethod
    def from_task(cls, task: Task):
        public_id = str(task.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "assigned_to_public_id": str(task.assigned_to_public_id),
            },
        )


@dataclass
class TaskCompleted(BaseTaskBusinessEvent):
    event_name = "TaskCompleted"

    @classmethod
    def from_task(cls, task: Task):
        public_id = str(task.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "assigned_to_public_id": str(task.assigned_to_public_id),
            },
        )

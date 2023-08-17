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
    event_version: ClassVar[int]
    key: str
    data: Optional[dict]

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_name": self.event_name,
                "event_version": self.event_version,
                "data": self.data,
            }
        )


@dataclass
class BaseTaskBusinessEvent(BaseEvent):
    topic = "tasks-lifecycle"


@dataclass
class NewTaskAddedV1(BaseTaskBusinessEvent):
    event_name = "NewTaskAdded"
    event_version = 1

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
class TaskReassignedV1(BaseTaskBusinessEvent):
    event_name = "TaskReassigned"
    event_version = 1

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
class TaskCompletedV1(BaseTaskBusinessEvent):
    event_name = "TaskCompleted"
    event_version = 1

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
class TaskCreatedV1(BaseEvent):
    topic = "tasks-stream"
    event_name = "Task.created"
    event_version = 1

    @classmethod
    def from_task(cls, task: Task):
        public_id = str(task.public_id)
        return cls(
            key=public_id,
            data={
                "public_id": public_id,
                "description": task.description,
                "jira_id": task.jira_id,
                "assignment_price": str(task.assignment_price),
                "completion_price": str(task.completion_price),
            },
        )

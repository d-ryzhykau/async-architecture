import json
from dataclasses import dataclass
from typing import ClassVar, List, Optional

from event_schema_registry import EventSchemaRegistry
from kafka import KafkaProducer

from .models import Task
from .settings import settings


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
                "assignment_price": str(task.assignment_price),
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
                "assignment_price": str(task.assignment_price),
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
                "completion_price": str(task.completion_price),
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

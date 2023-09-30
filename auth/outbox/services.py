from typing import Any

from event_schema_registry import EventSchemaRegistry

from .models import Event

event_schema_registry = EventSchemaRegistry()


def event_create(
    topic: str,
    name: str,
    version: int,
    key: str,
    data: Any,
) -> Event:
    """Validate `event` against schema registry and store it."""
    event_schema_registry.validate(
        topic=topic,
        event_name=name,
        event_version=version,
        data=data,
    )
    event = Event(topic=topic, name=name, version=version, key=key, data=data)
    event.save()
    return event

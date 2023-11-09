from typing import Sequence

from event_schema_registry import (
    EventSchemaRegistry,
    EventSchemaNotFound,
    EventSchemaValidationError,
)

from .models import Event

event_schema_registry = EventSchemaRegistry()


def event_bulk_create(events: Sequence[Event]):
    """Validate `events` against schema registry.
    If all events are valid, store them.

    Raises:
        ExceptionGroup: raised with all errors encountered on event validation.
    """
    validation_exceptions = []
    for event in events:
        try:
            event_schema_registry.validate(
                topic=event.topic,
                key=event.key,
                event_name=event.event_name,
                event_version=event.event_version,
                data=event.data,
            )
        except (EventSchemaNotFound, EventSchemaValidationError) as exc:
            validation_exceptions.append(exc)
    if validation_exceptions:
        raise ExceptionGroup("event_validation_exceptions", validation_exceptions)

    Event.objects.bulk_create(events)

import contextlib
import json
from functools import lru_cache
from importlib.resources import files
from typing import Optional

from jsonschema.protocols import Validator
from jsonschema.validators import validator_for
from jsonschema.exceptions import ValidationError


class EventSchemaValidationError(Exception):
    """Event validation against schema registry has failed."""


class EventSchemaNotFound(Exception):
    """Event schema was not found."""


# TODO: move common schemas to registry for reuse
class EventSchemaRegistry:
    def __init__(self, validator_cache_size=100):
        self._get_validator = (
            # add method wrapped in lru_cache as instance attribute
            # to achieve instance level caching
            lru_cache(validator_cache_size)(self._get_validator)
        )

    @staticmethod
    def _get_schema(topic: str, event_name: str, event_version: int):
        schema_path = (
            files("event_schema_registry.schemas")
            .joinpath(topic)
            .joinpath(event_name)
            .joinpath(f"{event_version}.json")
        )
        try:
            schema_file = schema_path.open("r")
        except FileNotFoundError:
            raise EventSchemaNotFound
        with contextlib.closing(schema_file):
            return json.load(schema_file)

    def _get_validator(
        self,
        topic: str,
        event_name: str,
        event_version: int,
    ) -> Validator:
        schema = self._get_schema(
            topic=topic,
            event_name=event_name,
            event_version=event_version,
        )
        validator_class = validator_for(schema)
        return validator_class(schema=schema)

    def validate(
        self,
        topic: str,
        event_name: str,
        event_version: int,
        event: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        """Validates event data against schema registry.

        Args:
            topic: name of the event topic.
            event_name: name of the event.
            event_version: version of the event.
            event: (deprecated, use `data` instead) complete event payload
                including its name, version and extra data.
            data: extra payload attached to the event.

        Raises:
            EventSchemaNotFound: if schema for given `topic`, `event_name`
                and `event_version` could not be found.
            EventSchemaValidationError: if event schema validation failed.
        """
        data_sources = [event, data]
        if not any(data_sources) or all(data_sources):
            raise ValueError("either 'event' or 'data' must be provided")

        if not event:
            event = {
                "event_name": event_name,
                "event_version": event_version,
                "data": data,
            }

        validator = self._get_validator(
            topic=topic,
            event_name=event_name,
            event_version=event_version,
        )
        try:
            validator.validate(event)
        except ValidationError:
            raise EventSchemaValidationError

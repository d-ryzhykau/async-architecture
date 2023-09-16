import json
from functools import lru_cache
from importlib.resources import files

from jsonschema.protocols import Validator
from jsonschema.validators import validator_for


# TODO: move common schemas to registry for reuse
class EventSchemaRegistry:
    def __init__(self, validator_cache_size=100):
        self._get_validator = lru_cache(validator_cache_size)(self._get_validator)

    @staticmethod
    def _get_schema(topic: str, event_name: str, event_version: int):
        schema_path = (
            files("event_schema_registry.schemas")
            .joinpath(topic)
            .joinpath(event_name)
            .joinpath(f"{event_version}.json")
        )
        with schema_path.open("r") as schema_file:
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

    def validate(self, topic: str, event_name: str, event_version: int, event: dict):
        self._get_validator(
            topic=topic,
            event_name=event_name,
            event_version=event_version,
        ).validate(event)

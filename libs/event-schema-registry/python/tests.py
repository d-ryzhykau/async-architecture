import json
import unittest
from importlib.resources import files

from jsonschema import SchemaError
from jsonschema.validators import validator_for


class TestEventSchemaRegistry(unittest.TestCase):
    def test_check_schemas(self):
        schema_errors = []
        for topic_dir in files("event_schema_registry.schemas").iterdir():
            for event_dir in topic_dir.iterdir():
                for version_file in event_dir.iterdir():
                    with version_file.open("r") as schema_file:
                        schema = json.load(schema_file)
                    validator_class = validator_for(schema)
                    try:
                        validator_class.check_schema(schema)
                    except SchemaError as exc:
                        schema_path = (
                            f"{topic_dir.name}"
                            f"/{event_dir.name}"
                            f"/{version_file.name}"
                        )
                        schema_errors.append(
                            {
                                "schema": schema_path,
                                "validator_class": validator_class,
                                "exception": exc,
                            }
                        )
        self.assertFalse(schema_errors)


if __name__ == "__main__":
    unittest.main()

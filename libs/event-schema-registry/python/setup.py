from setuptools import find_packages, setup

setup(
    name="event_schema_registry",
    version="0.3.0",
    python_requires=">=3.11",
    install_requires=[
        "jsonschema>=4.19.0,<5.0.0",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "event_schema_registry": ["schemas/*.json"],
    },
)

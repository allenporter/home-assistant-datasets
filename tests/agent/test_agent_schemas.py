import json
import jsonschema
from pathlib import Path


def validate(schema_path, example_path):
    schema = json.loads(Path(schema_path).read_text())
    example = json.loads(Path(example_path).read_text())
    jsonschema.validate(example, schema)


def test_home_ontology_examples():
    validate(
        "agents/ontology/v0/schemas/home_ontology.v0.schema.json",
        "agents/ontology/v0/examples/home_ontology.v0.examples.json"
    )


def test_entity_state_examples():
    for p in Path("agents/state/v0/examples").glob("*.json"):
        validate(
            "agents/state/v0/schemas/entity_state.v0.schema.json",
            p
        )

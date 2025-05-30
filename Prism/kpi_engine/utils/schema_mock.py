import json
from pathlib import Path

def load_mock_schema(schema_path=None):
    if schema_path is None:
        schema_path = Path(__file__).parent.parent / "mock_schema.json"
    with open(schema_path, "r") as f:
        return json.load(f) 
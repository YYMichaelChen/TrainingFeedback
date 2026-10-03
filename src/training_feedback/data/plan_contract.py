"""Load the packaged v4 schema; domain validation has no filesystem dependency."""

import json
from pathlib import Path


def plan_v4_schema():
    path = Path(__file__).resolve().parents[1] / "contracts" / "plan-v4.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))

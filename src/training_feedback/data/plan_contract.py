"""Load the packaged v2 schema; domain validation has no filesystem dependency."""

import json
from pathlib import Path


def plan_v2_schema():
    path = Path(__file__).resolve().parents[1] / "contracts" / "plan-v2.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))

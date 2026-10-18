"""Load current v5 and retained v4 schemas outside the pure domain layer."""

import json
from pathlib import Path


def plan_v4_schema():
    path = Path(__file__).resolve().parents[1] / "contracts" / "plan-v4.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def plan_v5_schema():
    path = Path(__file__).resolve().parents[1] / "contracts" / "plan-v5.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))

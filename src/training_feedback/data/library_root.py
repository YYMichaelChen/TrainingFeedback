"""当前模型数据根标记：新根初始化与已转换根校验。"""

from __future__ import annotations

import json
from pathlib import Path

from .catalog_resources import managed_path
from .data_root import CONFIG_FILENAME, DataRootError

LIBRARY_MODEL = "catalog-references-v1"


def initialize_library_root(path: Path) -> None:
    for directory in ("custom-exercise-images", "snapshot-assets"):
        managed_path(path, directory).mkdir(exist_ok=True)
    config_path = path / CONFIG_FILENAME
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["library_model"] = LIBRARY_MODEL
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def require_library_root(path: Path) -> None:
    config = json.loads((path / CONFIG_FILENAME).read_text(encoding="utf-8"))
    if config.get("library_model") != LIBRARY_MODEL:
        raise DataRootError("This root has not completed catalog-model conversion.")

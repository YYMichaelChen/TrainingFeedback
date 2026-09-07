"""只负责持久化“上一次有效数据根目录”位置的指针文件。"""

from __future__ import annotations

import json
import os
from pathlib import Path


class Locator:
    """数据根目录指针文件的读写。"""
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> Path | None:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                value = json.load(file)
            root = value.get("data_root")
            return Path(root) if isinstance(root, str) and root else None
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            return None

    def save(self, data_root: Path) -> None:
        """原子写入：先写临时文件再替换，避免中途失败留下半个 JSON。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            json.dump({"data_root": str(data_root)}, file, ensure_ascii=True, indent=2)
            file.write("\n")
        temporary.replace(self.path)


def default_locator_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = str(Path.home() / "AppData" / "Local")
    return Path(local_app_data) / "TrainingFeedback" / "locator.json"

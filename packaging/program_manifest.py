"""Write program ownership metadata for the exact completed directory payload."""

import argparse
import json
from pathlib import Path

from training_feedback import __version__
from training_feedback.data.installation import APP_ID, PROGRAM_MANIFEST, file_digest


def write_manifest(directory: Path) -> None:
    files = {
        path.relative_to(directory).as_posix(): file_digest(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != PROGRAM_MANIFEST
    }
    value = {"format": "training_feedback.program", "version": 1, "app_id": APP_ID,
             "application_version": __version__, "files": files}
    (directory / PROGRAM_MANIFEST).write_text(
        json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    write_manifest(parser.parse_args().directory)

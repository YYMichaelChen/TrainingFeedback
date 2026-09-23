"""Build the program catalog into a new/empty directory, or verify an existing payload."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_feedback.data.catalog_builder import build_catalog  # noqa: E402
from training_feedback.data.catalog_repository import CatalogRepository  # noqa: E402
from training_feedback.data.library_images import inspect_images  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if not args.verify:
        build_catalog(args.directory)
    with CatalogRepository(args.directory) as catalog:
        for entry in catalog.list():
            checks = inspect_images(entry["content"]["guidance"]["images"], catalog.image_bytes)
            if any(not check.valid and check.reason != "missing" for check in checks):
                raise ValueError("Catalog contains an invalid illustration.")
        print(f"Catalog verified: {catalog.version}, {len(catalog.list())} exercises")


if __name__ == "__main__":
    main()

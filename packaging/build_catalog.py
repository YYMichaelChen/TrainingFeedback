"""Build the program catalog into a new/empty directory, or verify an existing payload."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

def verify_files(directory: Path) -> None:
    """Compare owned resources to their manifest without exercising catalog rules."""
    directory = directory.resolve()
    manifest = json.loads((directory / "catalog-manifest.json").read_text(encoding="utf-8"))
    declared = {item["path"] for item in manifest["files"]}
    actual = {path.relative_to(directory).as_posix()
              for path in directory.rglob("*") if path.is_file()}
    if (len(declared) != len(manifest["files"])
            or "catalog.sqlite3" not in declared
            or actual != declared | {"catalog-manifest.json"}):
        raise ValueError("Catalog resource inventory does not match its manifest.")
    for item in manifest["files"]:
        path = (directory / item["path"]).resolve()
        if not path.is_relative_to(directory):
            raise ValueError("Catalog resource is outside the payload directory.")
        data = path.read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"Catalog resource identity differs: {item['path']}")
    print(f"Catalog resource identities match: {manifest['catalog_version']}, "
          f"{len(declared)} files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-files", action="store_true",
                        help="Only compare the resource inventory, sizes and hashes.")
    args = parser.parse_args()
    if args.verify_files:
        verify_files(args.directory)
        return
    from training_feedback.data.catalog_builder import build_catalog
    from training_feedback.data.catalog_repository import CatalogRepository
    from training_feedback.data.library_images import inspect_images

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

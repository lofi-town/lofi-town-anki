from __future__ import annotations

import argparse
import json
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "addon"
DEFAULT_OUTPUT = ROOT / "dist" / "lofi-town.ankiaddon"
REQUIRED_FILES = {
    "__init__.py",
    "manifest.json",
    "config.json",
    "resources/animations/cozy-bunny.gif",
    "resources/lofitownicon.png",
    "resources/fonts/BricolageGrotesqueVariable.woff2",
    "resources/licenses/OFL.txt",
    "web/cozy.css",
    "user_files/README.txt",
}


def package_files(addon_dir: Path = ADDON_DIR) -> list[Path]:
    files: list[Path] = []
    for path in addon_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(addon_dir)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if (
            relative.parts[0] == "user_files"
            and relative.as_posix() != "user_files/README.txt"
        ):
            continue
        files.append(path)
    return sorted(files)


def build_archive(output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files():
            relative = path.relative_to(ADDON_DIR).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes())
    validate_archive(output)
    return output


def validate_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_FILES - names
        if missing:
            raise ValueError(f"Package is missing: {', '.join(sorted(missing))}")
        if any(
            name.startswith("addon/")
            or "__pycache__" in name
            or name.endswith((".pyc", ".pyo"))
            for name in names
        ):
            raise ValueError("Package contains a wrapper directory or cache files.")
        unexpected_user_files = {
            name
            for name in names
            if name.startswith("user_files/") and name != "user_files/README.txt"
        }
        if unexpected_user_files:
            raise ValueError("Package contains persisted user data.")

        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("package") != "lofi_town_anki":
            raise ValueError("Package manifest has the wrong package name.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    if args.check:
        validate_archive(args.check)
        print(f"Valid package: {args.check}")
        return
    output = build_archive()
    print(f"Built {output}")


if __name__ == "__main__":
    main()

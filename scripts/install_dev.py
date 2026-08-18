from __future__ import annotations

import argparse
import os
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "addon"


def default_addons_dir() -> Path:
    override = os.environ.get("ANKI_ADDONS_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Anki2/addons21"
    if system == "Windows":
        app_data = os.environ.get("APPDATA")
        if not app_data:
            raise RuntimeError("APPDATA is unavailable. Set ANKI_ADDONS_DIR.")
        return Path(app_data) / "Anki2/addons21"
    return Path.home() / ".local/share/Anki2/addons21"


def install(addons_dir: Path) -> Path:
    destination = addons_dir / "lofi_town_anki"
    addons_dir.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() and destination.resolve() == SOURCE.resolve():
        return destination
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(
            f"Refusing to replace existing add-on path: {destination}"
        )
    destination.symlink_to(SOURCE, target_is_directory=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--addons-dir", type=Path, default=default_addons_dir())
    args = parser.parse_args()
    destination = install(args.addons_dir.expanduser())
    print(f"Installed development link: {destination}")


if __name__ == "__main__":
    main()

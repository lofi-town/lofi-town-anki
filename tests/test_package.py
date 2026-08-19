from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.package_addon import build_archive, validate_archive


def test_builds_flat_anki_addon_without_user_data(tmp_path: Path) -> None:
    output = build_archive(tmp_path / "lofi-town.ankiaddon")
    validate_archive(output)

    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
    assert "manifest.json" in names
    assert "__init__.py" in names
    assert "resources/animations/cozy-bunny.gif" in names
    assert "web/cozy.css" in names
    assert "session.py" in names
    assert "resources/fonts/BricolageGrotesqueVariable.woff2" in names
    assert "resources/fonts/BricolageGrotesque.ttf" not in names
    assert not any(name.startswith("addon/") for name in names)
    assert not any("__pycache__" in name for name in names)

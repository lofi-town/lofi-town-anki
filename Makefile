PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help bootstrap lint typecheck test qt-smoke package check-package install-dev clean

help:
	@echo "bootstrap      Create the development environment"
	@echo "lint           Run Ruff checks"
	@echo "typecheck      Run mypy"
	@echo "test           Run unit tests"
	@echo "qt-smoke       Construct the add-on UI with the installed aqt package"
	@echo "package        Build dist/lofi-town.ankiaddon"
	@echo "check-package  Validate the built package"
	@echo "install-dev    Symlink the add-on into the local Anki add-ons folder"
	@echo "clean          Remove generated development artifacts"

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e '.[dev]'

lint:
	$(BIN)/ruff check addon tests scripts

typecheck:
	$(BIN)/mypy addon scripts

test:
	$(BIN)/pytest

qt-smoke:
	PYTHONPATH=. QTWEBENGINE_DISABLE_SANDBOX=1 $(BIN)/python tests/qt_smoke.py

package:
	$(BIN)/python scripts/package_addon.py

check-package: package
	$(BIN)/python scripts/package_addon.py --check dist/lofi-town.ankiaddon

install-dev:
	$(BIN)/python scripts/install_dev.py

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache dist

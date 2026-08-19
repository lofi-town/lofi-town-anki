PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
RUN_PYTHON ?= $(BIN)/python
QT_SMOKE_ENV := QT_QPA_PLATFORM=offscreen \
	QTWEBENGINE_DISABLE_SANDBOX=1 \
	QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu

ifeq ($(shell uname -s),Darwin)
ANKI_APP ?= /Applications/Anki.app
QT_SMOKE_ENV += QT_PLUGIN_PATH="$(ANKI_APP)/Contents/Resources/app_packages/PyQt6/Qt6/plugins"
endif

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
	$(RUN_PYTHON) -m ruff check addon tests scripts

typecheck:
	$(RUN_PYTHON) -m mypy addon scripts

test:
	$(RUN_PYTHON) -m pytest

qt-smoke:
	PYTHONPATH=. $(QT_SMOKE_ENV) $(RUN_PYTHON) tests/qt_smoke.py

package:
	$(RUN_PYTHON) scripts/package_addon.py

check-package: package
	$(RUN_PYTHON) scripts/package_addon.py --check dist/lofi-town.ankiaddon

install-dev:
	$(RUN_PYTHON) scripts/install_dev.py

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache dist

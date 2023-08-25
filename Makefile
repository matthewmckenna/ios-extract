.PHONY: black black-check clean clean-logs coverage flake8 format install isort isort-check pip-compile test

SHELL := bash
.ONESHELL:
.DELETE_ON_ERROR:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

SRC_PYTHON := /Users/matthew/.pyenv/versions/3.12.0a7/bin/python
PIP_COMPILE := /Users/matthew/.local/bin/pip-compile --resolver backtracking --generate-hashes

PROJECT_NAME := iostoolbox
SRC_DIR := $(PROJECT_NAME)
TESTS_DIR := tests
VENV_DIR := .venv
EGG_INFO_DIR := $(PROJECT_NAME).egg-info

PYPROJECT_TOML := pyproject.toml

ISORT := isort --profile black

VENV_PIP := $(VENV_DIR)/bin/pip
VENV_PYTHON := $(VENV_DIR)/bin/python

black:
	black $(SRC_DIR) $(TESTS_DIR) --preview

black-check:
	black $(SRC_DIR) $(TESTS_DIR) --check --diff --color --preview -v

check: black-check

clean:
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(TESTS_DIR)/__pycache__
	rm -rf $(EGG_INFO_DIR)
	rm -rf .out/
	rm -rf .pytest_cache/

clean-logs:
	rm -r logs/*.log

coverage:
	pytest $(TESTS_DIR) --cov
	open .out/htmlcov/index.html

flake8:
	flake8 $(SRC_DIR) $(TESTS_DIR)

format: isort black

install: pip-compile
	rm -rf $(VENV_DIR)
	$(SRC_PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip setuptools
	$(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	$(VENV_PIP) install --editable .

isort:
	$(ISORT) $(SRC_DIR) $(TESTS_DIR)

isort-check:
	$(ISORT) --check $(SRC_DIR) $(TESTS_DIR)

pip-compile: requirements.txt requirements-dev.txt
	$(PIP_COMPILE) --output-file requirements.txt $(PYPROJECT_TOML)
	$(PIP_COMPILE) --output-file requirements-dev.txt --extra dev $(PYPROJECT_TOML)

test:
	pytest $(TESTS_DIR)

SHELL := /bin/bash
CURRENT_DATE = $(shell date +%Y%m%d_%H%M%S)
PYENV_DIR = ~/.pyenv
PYTHON_VERSION = 3.6.8
PYTHON_BASE = $(PYENV_DIR)/versions/$(PYTHON_VERSION)/bin/python
PYTHON_BIN = ./venv/bin
PYTHON_INTERPRETER = $(PYTHON_BIN)/python

all: venv test deploy

venv: venv/bin/python
	$(PYTHON_INTERPRETER) -m pip install --upgrade pip
	$(PYTHON_INTERPRETER) -m pip install -e .
	$(PYTHON_INTERPRETER) -m pip install django==3.2.25

venv/bin/python:
	$(PYENV_DIR)/bin/pyenv install $(PYTHON_VERSION) -s
	$(PYTHON_BASE) -m venv venv

test: venv
	(source $(PYTHON_BIN)/activate && cd testproj && ./manage.py test testapp auth_media)

deploy: venv
	$(PYTHON_INTERPRETER) setup.py sdist

clean:
	rm -rf venv
	rm -rf dist

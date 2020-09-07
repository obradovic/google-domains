.PHONY: .

SHELL := /bin/bash
TIMER = TIMEFORMAT="This make target took %1R seconds" && time  # bash built-in, requires bash to be the SHELL above


all: black ci
	@echo ""
	@echo "ALL GOOD!"
	@echo ""

ci: blackcheck typecheck pep lint test coverage

black:
	@$(TIMER) black *.py

blackcheck:
	@$(TIMER) black --check *.py

lint:
	@$(TIMER) pylint_runner -v --rcfile .pylintrc .

pep:
	@$(TIMER) pycodestyle *.py

typecheck:
	@$(TIMER) mypy *.py

coverage: coverage-run coverage-report

coverage-run:
	@$(TIMER) coverage run --source=. -m pytest -c setup.cfg --durations=5 -vv .
	@# @py.test --cov-report term-missing --cov=. .

coverage-report:
	@echo
	@echo
	@$(TIMER) coverage report -m

test:
	@$(TIMER) py.test .

run:
	@$(TIMER) ./google-domains-api

clean:
	@rm -rf .coverage .mypy_cache .pytest_cache __pycache__ build dist *.egg-info

#
# Below this, things are only useful for wheel management
#
wheel: wheel-build wheel-install

# Builds the wheel
wheel-build:
	@rm -f dist/*.whl
	@python3 setup.py bdist_wheel

# Installs the wheel
wheel-install:
	@python3 -m pip install --force dist/*.whl

# Uploads to pypi
wheel-push:
	@python3 -m twine upload dist/*.whl

# Initializes the environment - only need to run once
init:
	@python3 -m virtualenv .env
	@python3 -m pip install --upgrade pip setuptools wheel tqdm twine
	@python3 -m pip install -r requirements.txt


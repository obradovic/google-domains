.PHONY: .

SHELL := /bin/bash
TIMER = TIMEFORMAT="This make target took %1R seconds" && time  # bash built-in, requires bash to be the SHELL above
SRC := google_domains/*.py
PYTHONPATH = export PYTHONPATH=.

# https://stackoverflow.com/questions/2214575/passing-arguments-to-make-run
ifeq (run,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif


all: black ci
	@echo ""
	@echo "ALL GOOD!"
	@echo ""

ci: blackcheck mypy pep lint coverage

black:
	@$(TIMER) black $(SRC)

blackcheck:
	@$(TIMER) black --check $(SRC)

lint:
	@$(PYTHONPATH) $(TIMER) pylint_runner -v --rcfile .pylintrc .

pep:
	@$(TIMER) pycodestyle $(SRC)

mypy:
	@$(TIMER) mypy $(SRC)

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

# ie. make run -- -v --browser firefox ls
run:
	@$(PYTHONPATH) $(TIMER) python google_domains/command_line.py $(RUN_ARGS)

clean:
	@rm -rf .coverage .mypy_cache .pytest_cache __pycache__ build dist *.egg-info geckodriver.log

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
	@python3 -m pip install -r requirements.txt
	@python3 -m pip install --upgrade pip setuptools wheel tqdm twine


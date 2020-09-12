.PHONY: .

SHELL := /bin/bash
TIMER = TIMEFORMAT="This make target took %1R seconds" && time  # bash built-in, requires bash to be the SHELL above
SRC := google_domains/*.py
WHEEL := dist/*.whl
PYTHON := python3
PIP_INSTALL := $(PYTHON) -m pip install
PYTHONPATH = export PYTHONPATH=.
DOCKER_IMAGE := zoooo/google-domains
DOCKER_LATEST := $(DOCKER_IMAGE):latest
VERSION := $(shell cat VERSION)


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
	@$(PYTHONPATH) $(TIMER) $(PYTHON) google_domains/command_line.py $(RUN_ARGS)

clean:
	@rm -rf .coverage .mypy_cache .pytest_cache __pycache__ build dist *.egg-info geckodriver.log

publish: wheel-build wheel-push docker-build docker-push
	@echo ""
	@echo "PUBLISHED!"
	@echo ""



#
# Docker
#
docker-bash:
	@docker container run -it $(DOCKER_LATEST)

docker-build: # clean ci wheel-build
	@DOCKER_BUILDKIT=1 docker image build -t $(DOCKER_IMAGE):$(VERSION) -t $(DOCKER_LATEST) .

docker-push:
	@docker image push $(DOCKER_IMAGE)


#
# Below this, things are only useful for wheel management
#
wheel: clean ci wheel-build wheel-install

# Builds the wheel
wheel-build:
	@rm -f $(WHEEL)
	@$(PYTHON) setup.py bdist_wheel

# Installs the wheel
wheel-install:
	@$(PIP_INSTALL) --force $(WHEEL)

# Uploads to pypi
wheel-push: wheel-build
	@$(PYTHON) -m twine upload $(WHEEL)

# Initializes the environment - only need to run once
init:
	@$(PYTHON) -m virtualenv .env
	@$(PIP_INSTALL) -r requirements.txt
	@$(PIP_INSTALL) --upgrade pip setuptools wheel tqdm twine


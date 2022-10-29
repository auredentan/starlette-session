.DEFAULT_GOAL := help

PY_SRC := starlette_session/ tests/ examples/
CI ?= false
TESTING ?= false

.PHONY: help
help:  ## Print this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: clean
clean:  ## Delete temporary files.
	@rm -rf build 2>/dev/null
	@rm -rf .coverage* 2>/dev/null
	@rm -rf dist 2>/dev/null
	@rm -rf .mypy_cache 2>/dev/null
	@rm -rf pip-wheel-metadata 2>/dev/null
	@rm -rf .pytest_cache 2>/dev/null
	@rm -rf starlette_session/*.egg-info 2>/dev/null
	@rm -rf starlette_session/__pycache__ 2>/dev/null
	@rm -rf site 2>/dev/null
	@rm -rf tests/__pycache__ 2>/dev/null
	@rm -rf *.egg-info 2>/dev/null
	@find . -name "*.rej" -delete 2>/dev/null

##
# Docs
## 

.PHONY: docs
docs: doc-regen  ## Build the documentation locally.
	@poetry run mkdocs build

.PHONY: doc-regen
doc-regen: 
	cp README.md docs/index.md

.PHONY: docs-serve
docs-serve: doc-regen  ## Serve the documentation (localhost:8000).
	@poetry run mkdocs serve

.PHONY: doc-deploy
docs-deploy: doc-regen  ## Deploy the documentation on GitHub pages.
	@poetry run mkdocs gh-deploy

.PHONY: changelog
changelog:  ## Update the changelog in-place with latest commits.
	@poetry run python scripts/update_changelog.py \
		CHANGELOG.md "<!-- insertion marker -->" "^## \[(?P<version>[^\]]+)"

##
# Checks
##

.PHONY: check
check: check-docs check-types ## Check it all!

.PHONY: check-docs
check-docs:  ## Check if the documentation builds correctly.
	@poetry run mkdocs build

.PHONY: check-types
check-types:  ## Check that the code is correctly typed.
	@poetry run mypy --config-file=./config/mypy.ini $(PY_SRC)

##
# Setup
##

.PHONY: setup
setup:  ## Setup the development environment (install dependencies).
	@if ! $(CI); then \
		if ! command -v poetry &>/dev/null; then \
		  if ! command -v pipx &>/dev/null; then \
			  pip install --user pipx; \
			fi; \
		  pipx install poetry; \
		fi; \
	fi; \
	poetry install -v
	@if ! $(CI); then \
		poetry run pre-commit install; \
	fi;
	
.PHONY: format
format:  ## Run formatting tools on the code.
	@poetry run black $(PY_SRC)
	@poetry run isort -rc $(PY_SRC)


.PHONY: release
release:  ## Create a new release (commit, tag, push, build, publish, deploy docs).
ifndef v
	$(error Pass the new version with 'make release v=0.0.0')
endif
	@poetry run poetry version $(v)
	@poetry run git add pyproject.toml CHANGELOG.md
	@poetry run git commit -m ":package: Prepare release $(v) :package:"
	@poetry run git tag v$(v)
	@poetry run poetry build
	-@if ! $(CI) && ! $(TESTING); then \
		poetry run git push; \
		poetry run git push --tags; \
		poetry run poetry publish; \
		poetry run poetry run mkdocs gh-deploy; \
	fi


.PHONY: test
test:  ## Run the test suite and report coverage.
	@poetry run pytest --cov starlette_session

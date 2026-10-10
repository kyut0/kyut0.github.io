.PHONY: install lint format typecheck test check validate build serve themes typing clean

install:  ## Install dependencies and git hooks
	poetry install
	poetry run pre-commit install

lint:
	poetry run ruff check .
	poetry run ruff format --check .

format:
	poetry run ruff check --fix .
	poetry run ruff format .

typecheck:
	poetry run mypy

test:
	poetry run pytest --cov=portfolio --cov-report=term-missing

check: lint typecheck test  ## Everything CI runs

validate:
	poetry run portfolio validate

build:  ## Fresh build, so deleted pages don't linger
	rm -rf _site
	poetry run portfolio build

serve:
	rm -rf _site
	poetry run portfolio serve

themes:  ## Check site/themes.yaml and write _site/themes-preview.html
	poetry run portfolio themes

typing:  ## Refresh content/typing.yaml from Monkeytype
	poetry run portfolio typing

clean:
	rm -rf _site .pytest_cache .mypy_cache .ruff_cache .coverage

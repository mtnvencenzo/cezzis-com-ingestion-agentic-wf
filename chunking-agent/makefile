.PHONY: install update build lint format test test coverage cocktails-api standards all

install:
	poetry install --with dev

update:
	poetry update

build:
	poetry build

lint:
	poetry run ruff check --fix . --config .ruff.toml

format:
	poetry run ruff format . --config .ruff.toml

test:
	poetry run pytest

coverage:
	poetry run pytest -v --cov=cocktails_chunking_agent --cov-report=xml:coverage.xml --cov-report=term --junitxml=pytest-results.xml

gen-cocktails-api:
	poetry run datamodel-codegen \
		--url "http://localhost:7177/scalar/v1/openapi.json" \
		--input-file-type openapi --output src/cocktails_chunking_agent/infrastructure/clients/cocktails_api/cocktail_api.py \
		--output-model-type pydantic_v2.BaseModel \
		--field-constraints --use-default \
		--use-schema-description \
		--target-python-version 3.12

standards:
	@make lint
	@echo "Code standards check complete."
	@make format
	@echo "Code formatting complete."

all:
	@make install
	@make cocktails-api
	@make standards
	@make coverage
	@make build
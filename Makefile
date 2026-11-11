.PHONY: install lint format test up down explore sample

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest -q

up:
	docker compose up -d

down:
	docker compose down

explore:
	uv run python -I scripts/explore_metadata.py

sample:
	uv run python -I scripts/sample_fulltext.py

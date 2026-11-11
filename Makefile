.PHONY: install lint format test up down explore

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
	uv run python scripts/explore_metadata.py

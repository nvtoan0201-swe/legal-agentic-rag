.PHONY: install lint format test up down explore sample ingest load-db test-db eval-data check-eval

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

ingest:
	uv run python -I scripts/ingest.py

load-db:
	uv run python -I scripts/load_db.py

# Integration test on a throwaway database (the test drops and recreates tables).
test-db:
	docker compose exec -T postgres psql -U legalrag -tc "SELECT 1 FROM pg_database WHERE datname='legalrag_test'" | grep -q 1 || docker compose exec -T postgres createdb -U legalrag legalrag_test
	LEGALRAG_TEST_DSN=postgresql://legalrag:legalrag@localhost:55432/legalrag_test uv run pytest -q tests/test_db.py

eval-data:
	uv run python -I scripts/build_eval.py

check-eval:
	uv run python -I scripts/check_eval_set.py eval/sets/*.jsonl

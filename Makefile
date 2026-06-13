.PHONY: check lint test fmt install bench

install:
	uv pip install -e ".[dev]"

lint:
	ruff check sentinel tests bench

fmt:
	ruff format sentinel tests bench

test:
	pytest

check: lint test

bench:
	python -m bench.run

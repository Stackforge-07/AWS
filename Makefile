.PHONY: setup dev api ui build test test-edge train train-edge evaluate generate-data replay-demo benchmark-edge
setup:
	uv sync --python 3.12
	cd frontend && npm ci
api:
	uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8010
ui:
	cd frontend && npm run dev
dev:
	./scripts/dev.sh
build:
	cd frontend && npm run build
test:
	uv run pytest -q
	$(MAKE) test-edge
test-edge:
	c++ -std=c++17 -Wall -Wextra -pedantic edge/tests/test_edge.cpp -o /tmp/skyguard-edge-tests
	/tmp/skyguard-edge-tests
train:
	uv run python ml/train.py
train-edge:
	uv run --with tensorflow==2.20.0 --with 'numpy<2.3' python ml/train_edge.py
evaluate:
	uv run python ml/evaluate.py
generate-data:
	uv run python scripts/generate_data.py
replay-demo:
	uv run python scripts/replay_demo.py
benchmark-edge:
	uv run --with tensorflow==2.20.0 --with 'numpy<2.3' python scripts/benchmark_edge.py

.PHONY: expand-dataset evaluate-archive
expand-dataset:
	uv run python scripts/expand_dataset.py
evaluate-archive:
	uv run python ml/evaluate_archive.py

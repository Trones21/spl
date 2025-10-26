### 🧪 Testing Across Plugins

SPL’s test suite includes both **core** unit tests and **adapter-specific** integration tests.
Each plugin has its own environment and test layer, so you can run only what’s relevant to your setup.

| Scope                             | Location                           | Command                                  | Notes                                                |
| --------------------------------- | ---------------------------------- | ---------------------------------------- | ---------------------------------------------------- |
| **Core unit tests**               | `SPL/` (repo root)                 | `poetry run pytest -v`                   | Fast, adapter-independent tests.                     |
| **Hyperliquid integration tests** | `plugins/spl-adapter-hyperliquid/` | `poetry run pytest -m integration -v`    | Requires internet; hits HL testnet WS.               |
| **Drift integration tests**       | `plugins/spl-adapter-drift/`       | `poetry run pytest -m integration -v`    | Uses `driftpy` + testnet.                            |
| **Selective test run**            | Core                               | `poetry run pytest tests/test_engine.py` | Target individual test files.                        |

---

#### 🧭 Integration test tagging

Integration tests are marked with `@pytest.mark.integration` in both core and plugin suites.
You can filter easily:

```bash
poetry run pytest -m integration
```

To skip them entirely (e.g. for CI fast mode):

```bash
poetry run pytest -m "not integration"
```

---

#### 🧩 Environment notes

* Each adapter plugin can have its own `.env` or config TOML file (e.g. `config/example.hyperliquid.toml`, `config/example.drift.toml`).
* Some integration tests require **network access** (e.g. WebSocket subscriptions).
  When running in CI, you can disable these using:

  ```bash
  export SKIP_NETWORK_TESTS=1
  ```

---

#### 🧪 Example: Full Hyperliquid smoke test

```bash
cd plugins/spl-adapter-hyperliquid
poetry shell
poetry run pytest -v -m integration
```

Expected output:

```
tests/test_hyperliquid_ws.py::test_hyperliquid_quotes_and_trades_smoke PASSED
```

### 🧰 Local Multi-Adapter Testing (two envs, one repo)

Because adapters pin different dependencies (e.g., `websockets 15` for Hyperliquid vs `driftpy → websockets 13`), it’s best to test each in its **own** virtualenv while sharing the same repo checkout.

#### Option A — with Poetry (recommended)

```bash
# 1) Core + Hyperliquid env
cd plugins/spl-adapter-hyperliquid
poetry env use python3.11
poetry install
# also install core (the CLI) into the same env
poetry run pip install -e ../../spl-trader
# run HL tests
poetry run pytest -v -m integration
# run core tests (from this env) if you want
poetry run pytest -v -k "not drift" ../../spl-trader/tests
deactivate  # if you used 'poetry shell'

# 2) Core + Drift env
cd ../spl-adapter-drift
poetry env use python3.11
poetry install
poetry run pip install -e ../../spl-trader
poetry run pytest -v -m integration
poetry run pytest -v -k "not hyperliquid" ../../spl-trader/tests
```

> Tip: `poetry shell` gives you an interactive shell in the env; use `exit` to leave it.

#### Option B — with venv + pip (also fine)

```bash
# Hyperliquid env
python3.11 -m venv .venv-hl
source .venv-hl/bin/activate
pip install -e spl-trader
pip install -e plugins/spl-adapter-hyperliquid
pytest -v -m integration plugins/spl-adapter-hyperliquid/tests
deactivate

# Drift env
python3.11 -m venv .venv-drift
source .venv-drift/bin/activate
pip install -e spl-trader
pip install -e plugins/spl-adapter-drift
pytest -v -m integration plugins/spl-adapter-drift/tests
deactivate
```

#### Sanity checks and common pitfalls

* **Which adapters are installed in this env?**

  ```bash
  python -c "from importlib.metadata import entry_points; print([e.name for e in entry_points(group='spl.adapters')])"
  ```
* **Avoid mixing adapters in one env.** If you install both plugins into the same env, dependency pins can conflict.
* **Network tests**: Integration tests need internet access (WS). To skip in CI:

  ```bash
  export SKIP_NETWORK_TESTS=1
  pytest -m "not integration"
  ```

#### Make it easy (optional Makefile)

```makefile
.PHONY: dev-hl dev-drift test-hl test-drift

dev-hl:
	python3.11 -m venv .venv-hl
	. .venv-hl/bin/activate && pip install -e spl-trader -e plugins/spl-adapter-hyperliquid

dev-drift:
	python3.11 -m venv .venv-drift
	. .venv-drift/bin/activate && pip install -e spl-trader -e plugins/spl-adapter-drift

test-hl:
	. .venv-hl/bin/activate && pytest -v -m integration plugins/spl-adapter-hyperliquid/tests

test-drift:
	. .venv-drift/bin/activate && pytest -v -m integration plugins/spl-adapter-drift/tests
```

Run:

```bash
make dev-hl && make test-hl
make dev-drift && make test-drift
```

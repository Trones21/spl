## ⚡ Environment & Installation (Poetry)

SPL uses **Poetry** for dependency management and reproducible builds.

### 1️⃣ Install Poetry (if not already installed)

```bash
pipx install poetry
# or:
pip install poetry
```

### 2️⃣ Configure the local environment

Keep the virtualenv inside the repo and target Python 3.11 (recommended for Drift & HL compatibility):

```bash
poetry config virtualenvs.in-project true
poetry env use python3.11
```

### 3️⃣ Install the Core (Engine & CLI)

```bash
poetry install
```

You can now verify the CLI entry point:

```bash
poetry run spl --help
```

---

## 🧩 Adapter Plugins

Adapters (e.g., Hyperliquid, Drift) are **separate Poetry packages** so their dependencies never conflict.
Install only the adapter(s) you need:

### 🔹 Hyperliquid

```bash
cd plugins/spl-adapter-hyperliquid
poetry install
```

This installs:

* `websockets >=15,<16`
* `orjson`, `anyio`, etc.

### 🔹 Drift

```bash
cd plugins/spl-adapter-drift
poetry install
```

This installs:

* `driftpy 0.8.80` (and `websockets ==13.0`)
* `anchorpy`, `solders`, etc.

> 🧠 Each adapter defines an entry point under `spl.adapters`, so the core auto-discovers it at runtime.

---

## 🧱 Typical Usage

Note: We need to be in the correct plugin folder to use the correct venv. This unfortunately means that traversing to get our config file is a bit ugly. (Later i could rewrite this so that it searches the config folder for the name... but thats just a quality of life thing...)

### Example: Hyperliquid paper mode

```bash
cd plugins/spl-adapter-hyperliquid
poetry run spl --config ../../config/example.hyperliquid.toml
```

### Example: Drift paper mode

```bash
cd plugins/spl-adapter-drift
poetry run spl --config ../../config/example.drift.toml
```

You’ll see a pre-run diagnostics summary:

```
[STORE] OK: writable at /home/user/gh/spl/spl.db
[ADAPTERS] installed: hyperliquid
[SPL] Running mode=paper exchange=hyperliquid symbol=SOL-PERP
```

---

## Docker

## 🐳 Running SPL in Docker

SPL ships with a ready-to-go `Dockerfile` and `docker-compose.yml` for local or server use.

### Build and run (runtime image)

```bash
docker compose up --build
````

This builds the lightweight **runtime** image (no Poetry, just the app + deps)
and launches the engine using your config in `config/example.shadow.toml`.

### Build and run (development mode)

If you want Poetry and dev dependencies available inside the container:

```bash
docker compose build --target dev
docker compose run --rm spl --config config/example.shadow.toml
```

### Notes

* Configs and source are **mounted** from your host, so changes are live.
* Logs and database (`spl.db`) will persist in the container unless mounted externally.
* To stop:

  ```bash
  docker compose down
  ```
* To tail logs:

  ```bash
  docker compose logs -f
  ```

💡 *Tip:* Adjust the `target:` in `docker-compose.yml` between `runtime` and `dev` depending on whether you want a fast, production-style build or an editable environment with Poetry.
   - optionally mount your whole repo with `- ./:/app`.

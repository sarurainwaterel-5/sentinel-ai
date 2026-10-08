# SentinelAI

SentinelAI is a knowledge and cognitive operating system built with React, FastAPI, PostgreSQL, Qdrant, and local sentence-transformer embeddings. It ingests PDFs, retrieves evidence, manages document lifecycle, and provides governed reasoning, planning, verification, and persistent reflection.

## Run on this computer

The local release uses Docker Compose for the complete application and keeps all published ports on `127.0.0.1`. The browser site has one administrator login.

Prerequisites: Docker Engine with Compose and Python 3.12 for repository tests (Python 3 is sufficient for initial credential setup). Docker downloads the application dependencies and embedding model on the first build.

```sh
python3 scripts/setup_local.py
./scripts/start_local.sh
```

Open **http://127.0.0.1:8080** and use the credentials in `.local/login.txt`. Credentials are generated once with private file permissions and excluded from Git. Settings in `.env.local` contain a random database password and a hashed administrator password. Never publish these files.

To enable Recall and model-assisted Reason, Plan, and Verify, configure `OPENAI_API_KEY` in `backend/.env`, then run `./scripts/start_local.sh` again. Without a key, these endpoints return a clear 503 configuration message; upload, semantic search, document management, and dashboard remain available. No API key is embedded in frontend assets.

Stop with `./scripts/stop_local.sh`. Containers restart with Docker. Data persists in Compose volumes for PostgreSQL, Qdrant, uploads, and cognitive history. Do not use `docker compose down -v` unless you intend to erase that data.

Troubleshooting:

```sh
docker compose --env-file .env.local -f docker-compose.local.yml ps
docker compose --env-file .env.local -f docker-compose.local.yml logs --tail=100 api
curl http://127.0.0.1:8011/ready
```

Port 8011 is the loopback API for local diagnostics. This installation is for one administrator on one computer. Public hosting requires TLS, network isolation, authentication at every reachable API boundary, provider credentials, backups and a separately verified production rollout.

## Development and verification

```sh
python3.12 -m venv backend/venv
backend/venv/bin/python -m pip install -r backend/requirements-dev.txt
backend/venv/bin/python scripts/cache_embeddings.py
cd backend
OPENAI_API_KEY=unit-test-placeholder DATABASE_URL=sqlite:///:memory: venv/bin/python -m pytest tests -q
cd ../frontend
npm ci
npm run lint
npm run test:run
npm run build
```

The placeholder key is for isolated tests only. Tests use doubles for model calls. The CPU requirements preserve application package pins while avoiding CUDA-only dependencies. Existing GPU requirements are retained separately in `backend/requirements.txt`.

Native development configuration examples live in `backend/.env.example` and `frontend/.env.example`. API and Alembic share `DATABASE_URL`; Qdrant uses `QDRANT_URL` and optional `QDRANT_API_KEY`. All frontend workspaces honor `VITE_API_URL`; the packaged browser build uses `/api` behind the authenticated reverse proxy.

## Current engineering boundary

Sprint 20.3 A–F and the semantic gate implementation exist. The independent human review is approved in commit `213fb04125b189adc2fc770f157e4e454b559644`. The 108-call independent semantic benchmark has not been completed. ADR-037 remains Proposed and propositions remain excluded from inference. Regression tests and a running local installation do not establish semantic judge accuracy.

See [the semantic evaluation protocol](backend/evaluation/semantic_judge/README.md), [Sprint 20.3](docs/sprints/Sprint-20.3-Governed-Semantic-Proposition-Generation.md), and [the local release report](docs/LOCAL_RELEASE.md).

Model-backed evaluation requires separate `SEMANTIC_JUDGE_API_KEY`, an explicit `SEMANTIC_JUDGE_MODEL`, and execution authorization. The judge runner intentionally does not read application dotenv settings or reuse the generation client.

Created by C. Titus-El (Saru El).

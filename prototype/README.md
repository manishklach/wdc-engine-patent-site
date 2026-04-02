# WDC-Engine Prototype

This directory contains a narrow MVP of the WDC-Engine concept described on the public GitHub Pages microsite.

The prototype demonstrates the central flow:

1. Multiple simulated agents submit tasks
2. Tasks are fingerprinted
3. Exact or near-duplicate tasks are detected
4. The first unique task enters a Temporal Admission Controller window
5. Sister tasks collapse into the same Shared Execution Unit
6. Backend execution runs once
7. The same result is fanned out to all subscribers
8. Metrics show deduplication multiplier and executions saved

## Architecture overview

- `backend/app/main.py`: FastAPI API and CORS setup
- `backend/app/engine.py`: TIR, SDE, TAC, CM, SEU-M, WIP-Cache mirroring, RFM behavior
- `backend/app/fingerprinting.py`: SFM logic for SQL, natural language, and API tasks
- `backend/app/scenarios.py`: Patent-aligned demo scenarios
- `frontend/`: Lightweight simulator UI for sending tasks and observing SEU state
- `docker-compose.yml`: Local bring-up for backend, Redis, and the static frontend

## Directory structure

```text
prototype/
  .env.example
  docker-compose.yml
  README.md
  backend/
    Dockerfile
    requirements.txt
    app/
      config.py
      engine.py
      fingerprinting.py
      main.py
      models.py
      scenarios.py
  frontend/
    index.html
    script.js
    styles.css
```

## Prerequisites

- Docker and Docker Compose, or
- Python 3.11+ and a local Redis instance

## Run locally

### Option 1: Docker Compose

1. Copy `.env.example` to `.env`.
2. From `prototype/`, run:

```powershell
docker compose up --build
```

3. Open the simulator at `http://localhost:4173`
4. The backend API will be available at `http://localhost:8000/api`

### Option 2: Run services manually

Backend:

```powershell
cd prototype\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd prototype\frontend
python -m http.server 4173
```

Redis:

- Start Redis locally on port `6379`, or
- Update `REDIS_URL` in `.env` to match your Redis instance

## Simulator scenarios

- `sql-collapse`: Three differently formatted but equivalent sales queries collapse into one SEU
- `nl-collapse`: Three differently worded support-ticket requests collapse by semantic similarity
- `unique-task`: A distinct task remains unique and executes independently

You can also submit tasks manually from the simulator form.

## Demo flow

The frontend shows:

- incoming tasks
- collapsed/shared tasks
- SEU states: `PENDING`, `EXECUTING`, `COMPLETED`, `FAILED`
- admission window progress
- result fan-out behavior
- deduplication metrics

## Limitations vs the full patent concept

- Single-node demo logic with light Redis lock simulation rather than a full distributed deployment
- Simplified SQL normalization stub rather than a full canonical SQL planner
- Embedding similarity is only used for natural-language tasks
- API canonicalization is intentionally lightweight
- The backend executor is mocked and returns representative payloads
- Metrics are demo-oriented and not tied to real infrastructure cost accounting

## Mapping from prototype modules to patent concepts

- `Task ingestion endpoint` -> `TIR`
- `fingerprinting.py` -> `SFM`
- Exact hash plus embedding similarity in `engine.py` -> `SDE`
- Delayed dispatch scheduling in `engine.py` -> `TAC`
- Subscriber attachment in `engine.py` -> `CM`
- Active SEU state plus Redis mirroring -> `WIP-Cache`
- One-time mock execution in `engine.py` -> `SEU-M`
- Shared result propagation back to task records -> `RFM`

## Notes

- This is a concept demo for local evaluation and explanation.
- It is designed to support the public microsite, not to represent a production deployment of the patent concept.

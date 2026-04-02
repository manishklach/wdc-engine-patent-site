from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine import WdcEngine
from .models import ScenarioLaunchResponse, StateSnapshot, TaskSubmission, TaskSubmissionResponse
from .scenarios import SCENARIOS

engine = WdcEngine()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await engine.connect()
    yield
    await engine.close()


app = FastAPI(
    title="WDC-Engine Prototype API",
    version="0.1.0",
    lifespan=lifespan,
    description="Prototype API for semantic deduplication and shared execution of agent-generated enterprise tasks.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/metrics")
async def metrics() -> dict:
    return engine.get_metrics().model_dump()


@app.get("/api/state", response_model=StateSnapshot)
async def state() -> StateSnapshot:
    return engine.get_state()


@app.get("/api/scenarios")
async def scenarios() -> list[dict[str, str]]:
    return engine.list_scenarios()


@app.post("/api/tasks", response_model=TaskSubmissionResponse)
async def submit_task(submission: TaskSubmission) -> TaskSubmissionResponse:
    return await engine.submit_task(submission)


@app.post("/api/scenarios/{scenario_name}", response_model=ScenarioLaunchResponse)
async def launch_scenario(scenario_name: str) -> ScenarioLaunchResponse:
    if scenario_name not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    return await engine.trigger_scenario(scenario_name)

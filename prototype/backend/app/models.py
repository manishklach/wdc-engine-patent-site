from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    SQL_QUERY = "SQL_QUERY"
    NATURAL_LANGUAGE = "NATURAL_LANGUAGE"
    API_CALL = "API_CALL"


class TaskLifecycle(str, Enum):
    RECEIVED = "RECEIVED"
    DEFERRED = "DEFERRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SEUStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskSubmission(BaseModel):
    agent_id: str = Field(..., min_length=1)
    task_type: TaskType
    payload: str = Field(..., min_length=1)


class FingerprintRecord(BaseModel):
    task_type: TaskType
    canonical: str
    exact_hash: str
    embedding: list[float] | None = None


class TaskRecord(BaseModel):
    task_id: str
    agent_id: str
    task_type: TaskType
    payload: str
    canonical: str
    exact_hash: str
    status: TaskLifecycle
    deferred: bool
    seu_id: str | None
    match_type: str | None = None
    created_at: float
    updated_at: float
    result: dict[str, Any] | None = None


class SEURecord(BaseModel):
    seu_id: str
    task_type: TaskType
    status: SEUStatus
    canonical: str
    exact_hash: str
    admission_window_ms: int
    created_at: float
    admission_deadline: float
    started_at: float | None = None
    completed_at: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    subscriber_task_ids: list[str] = Field(default_factory=list)
    subscriber_agent_ids: list[str] = Field(default_factory=list)
    match_reasons: list[str] = Field(default_factory=list)


class TaskSubmissionResponse(BaseModel):
    task_id: str
    seu_id: str
    status: TaskLifecycle
    deferred: bool
    match_type: str
    message: str


class MetricsSnapshot(BaseModel):
    total_tasks_received: int
    total_seus_executed: int
    executions_saved: int
    total_completed_tasks: int
    active_pending_seus: int
    active_executing_seus: int
    dedup_multiplier: float


class StateSnapshot(BaseModel):
    metrics: MetricsSnapshot
    tasks: list[TaskRecord]
    seus: list[SEURecord]


class ScenarioLaunchResponse(BaseModel):
    scenario: str
    scheduled_tasks: int
    description: str

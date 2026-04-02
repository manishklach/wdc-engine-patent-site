from __future__ import annotations

import asyncio
import json
import math
import time
import uuid
from typing import Any

import numpy as np
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config import settings
from .fingerprinting import cosine_similarity, fingerprint_task
from .models import (
    FingerprintRecord,
    MetricsSnapshot,
    SEURecord,
    SEUStatus,
    ScenarioLaunchResponse,
    StateSnapshot,
    TaskLifecycle,
    TaskRecord,
    TaskSubmission,
    TaskSubmissionResponse,
    TaskType,
)
from .scenarios import SCENARIOS


def _now() -> float:
    return time.time()


def _task_id() -> str:
    return f"task-{uuid.uuid4().hex[:8]}"


def _seu_id() -> str:
    return f"seu-{uuid.uuid4().hex[:8]}"


class WdcEngine:
    def __init__(self) -> None:
        self.tasks: dict[str, TaskRecord] = {}
        self.seus: dict[str, SEURecord] = {}
        self.embeddings: dict[str, np.ndarray] = {}
        self.redis: Redis | None = None
        self.lock = asyncio.Lock()
        self.total_tasks_received = 0
        self.total_seus_executed = 0
        self.executions_saved = 0

    async def connect(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await self.redis.ping()
        except RedisError:
            self.redis = None

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()

    async def submit_task(self, submission: TaskSubmission) -> TaskSubmissionResponse:
        fingerprint = fingerprint_task(submission.task_type, submission.payload)
        created_at = _now()
        task = TaskRecord(
            task_id=_task_id(),
            agent_id=submission.agent_id,
            task_type=submission.task_type,
            payload=submission.payload,
            canonical=fingerprint.canonical,
            exact_hash=fingerprint.exact_hash,
            status=TaskLifecycle.RECEIVED,
            deferred=False,
            seu_id=None,
            created_at=created_at,
            updated_at=created_at,
        )

        async with self.lock:
            self.total_tasks_received += 1
            self.tasks[task.task_id] = task
            matched_seu, match_type = self._find_match_locked(submission.task_type, fingerprint)
            if matched_seu is not None:
                return await self._collapse_locked(task, matched_seu, match_type)

            seu = await self._create_seu_locked(task, fingerprint)

        asyncio.create_task(self._dispatch_when_ready(seu.seu_id))
        return TaskSubmissionResponse(
            task_id=task.task_id,
            seu_id=seu.seu_id,
            status=task.status,
            deferred=False,
            match_type="UNIQUE",
            message="Task accepted into the Temporal Admission Controller.",
        )

    async def trigger_scenario(self, name: str) -> ScenarioLaunchResponse:
        scenario = SCENARIOS[name]
        asyncio.create_task(self._run_scenario(name))
        return ScenarioLaunchResponse(
            scenario=name,
            scheduled_tasks=len(scenario["tasks"]),
            description=scenario["description"],
        )

    async def _run_scenario(self, name: str) -> None:
        scenario = SCENARIOS[name]
        start = _now()
        for item in scenario["tasks"]:
            delay_s = item["delay_ms"] / 1000
            wait_for = start + delay_s - _now()
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            await self.submit_task(item["task"])

    def get_metrics(self) -> MetricsSnapshot:
        pending = sum(1 for seu in self.seus.values() if seu.status == SEUStatus.PENDING)
        executing = sum(1 for seu in self.seus.values() if seu.status == SEUStatus.EXECUTING)
        completed = sum(1 for task in self.tasks.values() if task.status == TaskLifecycle.COMPLETED)
        multiplier = 1.0
        if self.total_seus_executed:
            multiplier = self.total_tasks_received / self.total_seus_executed
        return MetricsSnapshot(
            total_tasks_received=self.total_tasks_received,
            total_seus_executed=self.total_seus_executed,
            executions_saved=self.executions_saved,
            total_completed_tasks=completed,
            active_pending_seus=pending,
            active_executing_seus=executing,
            dedup_multiplier=round(multiplier, 2),
        )

    def get_state(self) -> StateSnapshot:
        tasks = sorted(self.tasks.values(), key=lambda item: item.created_at, reverse=True)
        seus = sorted(self.seus.values(), key=lambda item: item.created_at, reverse=True)
        return StateSnapshot(metrics=self.get_metrics(), tasks=tasks, seus=seus)

    def list_scenarios(self) -> list[dict[str, str]]:
        return [{"name": name, "description": config["description"]} for name, config in SCENARIOS.items()]

    def _find_match_locked(self, task_type: TaskType, fingerprint: FingerprintRecord) -> tuple[SEURecord | None, str]:
        active_seus = [seu for seu in self.seus.values() if seu.status in {SEUStatus.PENDING, SEUStatus.EXECUTING}]
        for seu in active_seus:
            if seu.task_type == task_type and seu.exact_hash == fingerprint.exact_hash:
                return seu, "EXACT_HASH"

        if task_type != TaskType.NATURAL_LANGUAGE or fingerprint.embedding is None:
            return None, "UNIQUE"

        incoming = np.asarray(fingerprint.embedding)
        best_match: SEURecord | None = None
        best_score = -math.inf
        for seu in active_seus:
            existing = self.embeddings.get(seu.seu_id)
            if seu.task_type != TaskType.NATURAL_LANGUAGE or existing is None:
                continue
            score = cosine_similarity(incoming, existing)
            if score >= settings.nl_similarity_threshold and score > best_score:
                best_match = seu
                best_score = score

        if best_match is not None:
            return best_match, f"SEMANTIC_{best_score:.2f}"
        return None, "UNIQUE"

    async def _collapse_locked(self, task: TaskRecord, seu: SEURecord, match_type: str) -> TaskSubmissionResponse:
        task.seu_id = seu.seu_id
        task.deferred = seu.status in {SEUStatus.PENDING, SEUStatus.EXECUTING}
        task.status = TaskLifecycle.DEFERRED if task.deferred else TaskLifecycle.COMPLETED
        task.match_type = match_type
        task.updated_at = _now()
        if seu.result is not None:
            task.status = TaskLifecycle.COMPLETED
            task.deferred = False
            task.result = seu.result
        self.tasks[task.task_id] = task
        seu.subscriber_task_ids.append(task.task_id)
        seu.subscriber_agent_ids.append(task.agent_id)
        seu.match_reasons.append(match_type)
        self.seus[seu.seu_id] = seu
        await self._mirror_to_redis(seu)
        return TaskSubmissionResponse(
            task_id=task.task_id,
            seu_id=seu.seu_id,
            status=task.status,
            deferred=task.deferred,
            match_type=match_type,
            message="Task collapsed into an existing Shared Execution Unit.",
        )

    async def _create_seu_locked(self, task: TaskRecord, fingerprint: FingerprintRecord) -> SEURecord:
        seu_id = _seu_id()
        if not await self._acquire_lock(fingerprint, seu_id):
            matched = self._find_existing_exact_hash(fingerprint.exact_hash)
            if matched is not None:
                await self._collapse_locked(task, matched, "REDIS_LOCK_COLLAPSE")
                return matched

        window_ms = settings.admission_window_for(task.task_type.value)
        now = _now()
        seu = SEURecord(
            seu_id=seu_id,
            task_type=task.task_type,
            status=SEUStatus.PENDING,
            canonical=fingerprint.canonical,
            exact_hash=fingerprint.exact_hash,
            admission_window_ms=window_ms,
            created_at=now,
            admission_deadline=now + (window_ms / 1000),
            subscriber_task_ids=[task.task_id],
            subscriber_agent_ids=[task.agent_id],
            match_reasons=["UNIQUE"],
        )
        task.seu_id = seu.seu_id
        task.match_type = "UNIQUE"
        task.updated_at = now
        self.tasks[task.task_id] = task
        self.seus[seu.seu_id] = seu
        if fingerprint.embedding is not None:
            self.embeddings[seu.seu_id] = np.asarray(fingerprint.embedding)
        await self._mirror_to_redis(seu)
        return seu

    def _find_existing_exact_hash(self, exact_hash: str) -> SEURecord | None:
        for seu in self.seus.values():
            if seu.exact_hash == exact_hash and seu.status in {SEUStatus.PENDING, SEUStatus.EXECUTING}:
                return seu
        return None

    async def _dispatch_when_ready(self, seu_id: str) -> None:
        while True:
            async with self.lock:
                seu = self.seus.get(seu_id)
                if seu is None or seu.status != SEUStatus.PENDING:
                    return
                remaining = seu.admission_deadline - _now()
                if remaining <= 0:
                    seu.status = SEUStatus.EXECUTING
                    seu.started_at = _now()
                    self.seus[seu_id] = seu
                    await self._mirror_to_redis(seu)
                    break
            await asyncio.sleep(min(remaining, 0.1))

        exact_hash = seu.exact_hash
        try:
            result = await self._mock_backend_execute(seu)
            async with self.lock:
                fresh = self.seus[seu_id]
                fresh.status = SEUStatus.COMPLETED
                fresh.completed_at = _now()
                fresh.result = result
                self.seus[seu_id] = fresh
                self.total_seus_executed += 1
                self.executions_saved += max(0, len(fresh.subscriber_task_ids) - 1)
                for task_id in fresh.subscriber_task_ids:
                    task = self.tasks[task_id]
                    task.status = TaskLifecycle.COMPLETED
                    task.deferred = False
                    task.result = result
                    task.updated_at = fresh.completed_at or _now()
                    self.tasks[task_id] = task
                await self._mirror_to_redis(fresh)
        except Exception as exc:  # pragma: no cover
            async with self.lock:
                fresh = self.seus[seu_id]
                fresh.status = SEUStatus.FAILED
                fresh.error = str(exc)
                self.seus[seu_id] = fresh
                for task_id in fresh.subscriber_task_ids:
                    task = self.tasks[task_id]
                    task.status = TaskLifecycle.FAILED
                    task.updated_at = _now()
                    self.tasks[task_id] = task
                await self._mirror_to_redis(fresh)
        finally:
            await self._release_lock(exact_hash)

    async def _mock_backend_execute(self, seu: SEURecord) -> dict[str, Any]:
        await asyncio.sleep(1.15)
        if seu.task_type == TaskType.SQL_QUERY:
            rows = [
                {"customer_id": "C-1001", "total": 182400},
                {"customer_id": "C-1052", "total": 146900},
                {"customer_id": "C-1088", "total": 132050},
            ]
            summary = "Mock SQL executor returned a shared sales dataset."
        elif seu.task_type == TaskType.NATURAL_LANGUAGE:
            rows = [
                {"ticket_id": "ENT-301", "status": "in_progress"},
                {"ticket_id": "ENT-327", "status": "unresolved"},
                {"ticket_id": "ENT-402", "status": "resolved"},
            ]
            summary = "Mock retrieval executor returned enterprise support tickets."
        else:
            rows = [{"endpoint": "/v1/accounts/enrichment", "status": "ok", "records": 3}]
            summary = "Mock API executor returned a shared payload."
        return {
            "summary": summary,
            "task_type": seu.task_type.value,
            "canonical": seu.canonical,
            "rows": rows,
            "subscriber_count": len(seu.subscriber_task_ids),
        }

    async def _acquire_lock(self, fingerprint: FingerprintRecord, seu_id: str) -> bool:
        if self.redis is None:
            return True
        key = f"wdc:lock:{fingerprint.task_type.value}:{fingerprint.exact_hash}"
        try:
            acquired = await self.redis.set(key, seu_id, ex=15, nx=True)
            if acquired:
                lookup = f"wdc:lookup:{fingerprint.task_type.value}:{fingerprint.exact_hash}"
                await self.redis.set(lookup, seu_id, ex=60)
            return bool(acquired)
        except RedisError:
            return True

    async def _release_lock(self, exact_hash: str) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.delete(f"wdc:lock:SQL_QUERY:{exact_hash}")
            await self.redis.delete(f"wdc:lock:NATURAL_LANGUAGE:{exact_hash}")
            await self.redis.delete(f"wdc:lock:API_CALL:{exact_hash}")
        except RedisError:
            return

    async def _mirror_to_redis(self, seu: SEURecord) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.set(f"wdc:wip:{seu.seu_id}", json.dumps(seu.model_dump()), ex=3600)
        except RedisError:
            return

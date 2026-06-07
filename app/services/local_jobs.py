from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from app.tasks.generation import generate_voice_payload

JobRecord = dict[str, Any]
ProgressCallback = Callable[[str, int], None]


class LocalJobRunner:
    """Small in-process background runner for demos without Redis.

    This keeps the Generate button working on a plain Windows install while the
    Celery/Redis path remains available for production by setting
    BACKGROUND_BACKEND=celery.
    """

    def __init__(self, max_workers: int = 1) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="voice-local-job")
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def submit(self, payload: dict[str, Any]) -> str:
        job_id = uuid4().hex
        with self._lock:
            self._jobs[job_id] = {"job_id": job_id, "state": "PENDING", "stage": "queued", "percent": 0}
        self._executor.submit(self._run, job_id, payload)
        return job_id

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            record = self._jobs.get(job_id)
            return dict(record) if record else None

    def exists(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._jobs

    def _set(self, job_id: str, **updates: Any) -> None:
        with self._lock:
            self._jobs.setdefault(job_id, {"job_id": job_id}).update(updates)

    def _run(self, job_id: str, payload: dict[str, Any]) -> None:
        def progress(stage: str, percent: int) -> None:
            self._set(job_id, state="PROGRESS", stage=stage, percent=percent)

        try:
            progress("preparing", 5)
            result = generate_voice_payload(payload, progress=progress)
            self._set(job_id, state="SUCCESS", **result)
        except Exception as exc:  # noqa: BLE001 - surface local job failures to the UI.
            self._set(job_id, state="FAILURE", stage="failed", percent=100, error=str(exc))


local_jobs = LocalJobRunner(max_workers=1)

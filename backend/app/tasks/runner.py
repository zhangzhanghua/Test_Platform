import subprocess
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.core.config import settings
from app.core.pubsub import publish_log
from app.models.models import TestExecution, TestResult, TestCase, NotifyChannel, ExecutionStatus
from app.services.notify import notify_execution_complete
from app.tasks.celery_app import celery_app

sync_engine = create_engine(settings.SYNC_DATABASE_URL)


@celery_app.task(name="run_execution")
def run_execution(execution_id: str):
    with Session(sync_engine) as db:
        execution = db.get(TestExecution, execution_id)
        if not execution:
            return

        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        db.commit()
        publish_log(execution_id, "[START] Execution started")

        results = db.execute(
            select(TestResult).where(TestResult.execution_id == execution_id)
        ).scalars().all()

        passed = failed = 0

        for i, result in enumerate(results, 1):
            case = db.get(TestCase, result.case_id)
            publish_log(execution_id, f"[{i}/{len(results)}] Running: {case.title}")
            start = time.time()

            try:
                if case.script_path:
                    proc = subprocess.run(
                        ["python", case.script_path],
                        capture_output=True, text=True, timeout=300,
                    )
                    result.log = proc.stdout + proc.stderr
                    # stream stdout lines
                    for line in (proc.stdout or "").splitlines():
                        publish_log(execution_id, f"  | {line}")
                    if proc.returncode == 0:
                        result.status = ExecutionStatus.PASSED
                        passed += 1
                        publish_log(execution_id, f"  PASSED ({int((time.time()-start)*1000)}ms)")
                    else:
                        result.status = ExecutionStatus.FAILED
                        result.error_message = proc.stderr[-2000:] if proc.stderr else ""
                        failed += 1
                        publish_log(execution_id, f"  FAILED: {result.error_message[:200]}")
                else:
                    result.status = ExecutionStatus.SKIPPED
                    publish_log(execution_id, "  SKIPPED (no script)")
            except subprocess.TimeoutExpired:
                result.status = ExecutionStatus.ERROR
                result.error_message = "Timeout after 300s"
                failed += 1
                publish_log(execution_id, "  ERROR: Timeout after 300s")
            except Exception as e:
                result.status = ExecutionStatus.ERROR
                result.error_message = str(e)[:2000]
                failed += 1
                publish_log(execution_id, f"  ERROR: {str(e)[:200]}")

            result.duration_ms = int((time.time() - start) * 1000)
            db.commit()

        execution.passed = passed
        execution.failed = failed
        execution.status = ExecutionStatus.PASSED if failed == 0 else ExecutionStatus.FAILED
        execution.finished_at = datetime.now(timezone.utc)
        execution.duration_ms = int((execution.finished_at - execution.started_at).total_seconds() * 1000)
        db.commit()

        summary = f"[DONE] Passed: {passed}, Failed: {failed}, Duration: {execution.duration_ms}ms"
        publish_log(execution_id, summary)

        # Send notifications
        channels = db.execute(
            select(NotifyChannel).where(NotifyChannel.is_active == True)
        ).scalars().all()
        if channels:
            ch_list = [{"name": c.name, "channel_type": c.channel_type.value, "config": c.config} for c in channels]
            notify_execution_complete(
                execution_name=execution.name,
                status=execution.status.value,
                total=execution.total,
                passed=passed,
                failed=failed,
                duration_ms=execution.duration_ms,
                channels=ch_list,
            )

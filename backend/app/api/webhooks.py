from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role
from app.models.models import User, Webhook, TestSuite, TestCase, TestExecution, TestResult
from app.schemas.schemas import WebhookCreate, WebhookOut, WebhookTriggerResponse
from app.tasks.runner import run_execution

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ── Management (auth required) ─────────────────────────

@router.get("", response_model=list[WebhookOut])
async def list_webhooks(db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    result = await db.execute(select(Webhook).order_by(Webhook.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=WebhookOut)
async def create_webhook(body: WebhookCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "manager"))):
    suite = await db.get(TestSuite, body.suite_id)
    if not suite:
        raise HTTPException(400, "Suite not found")
    wh = Webhook(**body.model_dump(), created_by=user.id)
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return wh


@router.patch("/{webhook_id}", response_model=WebhookOut)
async def toggle_webhook(webhook_id: UUID, is_active: bool, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    wh = await db.get(Webhook, webhook_id)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    wh.is_active = is_active
    await db.commit()
    await db.refresh(wh)
    return wh


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    wh = await db.get(Webhook, webhook_id)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    await db.delete(wh)
    await db.commit()
    return {"ok": True}


# ── Trigger (no auth, token-based) ─────────────────────

@router.post("/{token}/trigger", response_model=WebhookTriggerResponse)
async def trigger_webhook(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    wh = await db.scalar(select(Webhook).where(Webhook.token == token))
    if not wh:
        raise HTTPException(404, "Webhook not found")
    if not wh.is_active:
        raise HTTPException(403, "Webhook is disabled")

    # Get payload (optional overrides from CI)
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    execution_name = payload.get("name", f"Webhook: {wh.name}")

    # Fetch all cases in the suite
    cases = (await db.execute(
        select(TestCase).where(TestCase.suite_id == wh.suite_id)
    )).scalars().all()

    if not cases:
        raise HTTPException(400, "No test cases in suite")

    execution = TestExecution(
        name=execution_name,
        trigger_by=wh.created_by,
        environment_id=wh.environment_id,
        total=len(cases),
    )
    db.add(execution)
    await db.flush()

    for case in cases:
        db.add(TestResult(execution_id=execution.id, case_id=case.id))

    await db.commit()
    await db.refresh(execution)

    run_execution.delay(str(execution.id))

    return WebhookTriggerResponse(
        execution_id=execution.id,
        message=f"Triggered {len(cases)} test cases",
    )

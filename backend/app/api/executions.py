from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, TestExecution, TestResult, TestCase, ExecutionStatus
from app.schemas.schemas import ExecutionCreate, ExecutionOut, TestResultOut
from app.tasks.runner import run_execution

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=list[ExecutionOut])
async def list_executions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestExecution).order_by(TestExecution.created_at.desc()).limit(50))
    return result.scalars().all()


@router.post("", response_model=ExecutionOut)
async def create_execution(body: ExecutionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    execution = TestExecution(
        name=body.name,
        trigger_by=user.id,
        environment_id=body.environment_id,
        total=len(body.case_ids),
    )
    db.add(execution)
    await db.flush()

    for cid in body.case_ids:
        case = await db.get(TestCase, cid)
        if not case:
            raise HTTPException(400, f"Case {cid} not found")
        db.add(TestResult(execution_id=execution.id, case_id=cid))

    await db.commit()
    await db.refresh(execution)

    # trigger async execution
    run_execution.delay(str(execution.id))
    return execution


@router.get("/{execution_id}", response_model=ExecutionOut)
async def get_execution(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    execution = await db.get(TestExecution, execution_id)
    if not execution:
        raise HTTPException(404, "Execution not found")
    return execution


@router.get("/{execution_id}/results", response_model=list[TestResultOut])
async def get_results(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestResult).where(TestResult.execution_id == execution_id))
    return result.scalars().all()

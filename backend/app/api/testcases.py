from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, TestSuite, TestCase
from app.schemas.schemas import (
    TestSuiteCreate, TestSuiteOut,
    TestCaseCreate, TestCaseUpdate, TestCaseOut,
)

router = APIRouter(prefix="/testcases", tags=["testcases"])


# ── Suites ─────────────────────────────────────────────

@router.get("/suites", response_model=list[TestSuiteOut])
async def list_suites(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestSuite).where(TestSuite.project_id == project_id))
    return result.scalars().all()


@router.post("/suites", response_model=TestSuiteOut)
async def create_suite(body: TestSuiteCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    suite = TestSuite(**body.model_dump())
    db.add(suite)
    await db.commit()
    await db.refresh(suite)
    return suite


# ── Cases ──────────────────────────────────────────────

@router.get("/cases", response_model=list[TestCaseOut])
async def list_cases(suite_id: UUID, tab_node_id: UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(TestCase).where(TestCase.suite_id == suite_id).order_by(TestCase.created_at.desc())
    if tab_node_id:
        q = q.where(TestCase.tab_node_id == tab_node_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/cases", response_model=TestCaseOut)
async def create_case(body: TestCaseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    case = TestCase(**body.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/cases/{case_id}", response_model=TestCaseOut)
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    case = await db.get(TestCase, case_id)
    if not case:
        raise HTTPException(404, "TestCase not found")
    return case


@router.patch("/cases/{case_id}", response_model=TestCaseOut)
async def update_case(case_id: UUID, body: TestCaseUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    case = await db.get(TestCase, case_id)
    if not case:
        raise HTTPException(404, "TestCase not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(case, k, v)
    await db.commit()
    await db.refresh(case)
    return case


@router.delete("/cases/{case_id}")
async def delete_case(case_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    case = await db.get(TestCase, case_id)
    if not case:
        raise HTTPException(404, "TestCase not found")
    await db.delete(case)
    await db.commit()
    return {"ok": True}

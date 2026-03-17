from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Environment
from app.schemas.schemas import EnvironmentCreate, EnvironmentOut

router = APIRouter(prefix="/environments", tags=["environments"])


@router.get("", response_model=list[EnvironmentOut])
async def list_environments(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Environment).where(Environment.project_id == project_id))
    return result.scalars().all()


@router.post("", response_model=EnvironmentOut)
async def create_environment(body: EnvironmentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    env = Environment(**body.model_dump())
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return env


@router.get("/{env_id}", response_model=EnvironmentOut)
async def get_environment(env_id: UUID, db: AsyncSession = Depends(get_db)):
    env = await db.get(Environment, env_id)
    if not env:
        raise HTTPException(404, "Environment not found")
    return env


@router.put("/{env_id}", response_model=EnvironmentOut)
async def update_environment(env_id: UUID, body: EnvironmentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    env = await db.get(Environment, env_id)
    if not env:
        raise HTTPException(404, "Environment not found")
    for k, v in body.model_dump().items():
        setattr(env, k, v)
    await db.commit()
    await db.refresh(env)
    return env


@router.delete("/{env_id}")
async def delete_environment(env_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    env = await db.get(Environment, env_id)
    if not env:
        raise HTTPException(404, "Environment not found")
    await db.delete(env)
    await db.commit()
    return {"ok": True}

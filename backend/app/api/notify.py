from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role
from app.models.models import User, NotifyChannel
from app.schemas.schemas import NotifyChannelCreate, NotifyChannelUpdate, NotifyChannelOut

router = APIRouter(prefix="/notify-channels", tags=["notify"])


@router.get("", response_model=list[NotifyChannelOut])
async def list_channels(project_id: Optional[UUID] = None, db: AsyncSession = Depends(get_db)):
    q = select(NotifyChannel).order_by(NotifyChannel.created_at.desc())
    if project_id:
        q = q.where(NotifyChannel.project_id == project_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=NotifyChannelOut)
async def create_channel(body: NotifyChannelCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    ch = NotifyChannel(**body.model_dump())
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch


@router.patch("/{channel_id}", response_model=NotifyChannelOut)
async def update_channel(channel_id: UUID, body: NotifyChannelUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    ch = await db.get(NotifyChannel, channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ch, k, v)
    await db.commit()
    await db.refresh(ch)
    return ch


@router.delete("/{channel_id}")
async def delete_channel(channel_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    ch = await db.get(NotifyChannel, channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")
    await db.delete(ch)
    await db.commit()
    return {"ok": True}


@router.post("/{channel_id}/test")
async def test_channel(channel_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin", "manager"))):
    ch = await db.get(NotifyChannel, channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")
    from app.services.notify import notify_execution_complete
    notify_execution_complete(
        execution_name="测试通知",
        status="passed", total=10, passed=9, failed=1, duration_ms=1234,
        channels=[{"name": ch.name, "channel_type": ch.channel_type.value, "config": ch.config}],
    )
    return {"ok": True, "message": "Test notification sent"}

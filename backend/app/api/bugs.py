import os
import uuid as _uuid
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Bug, BugComment, BugAttachment, BugStatus, BugSeverity
from app.schemas.schemas import (
    BugCreate, BugUpdate, BugOut, BugStatusTransition, BugStats,
    BugCommentCreate, BugCommentOut, BugAttachmentOut,
)

router = APIRouter(prefix="/bugs", tags=["bugs"])

VALID_TRANSITIONS: dict[BugStatus, list[BugStatus]] = {
    BugStatus.OPEN: [BugStatus.IN_PROGRESS, BugStatus.REJECTED],
    BugStatus.IN_PROGRESS: [BugStatus.FIXED, BugStatus.OPEN],
    BugStatus.FIXED: [BugStatus.VERIFIED, BugStatus.IN_PROGRESS],
    BugStatus.VERIFIED: [BugStatus.CLOSED, BugStatus.IN_PROGRESS],
    BugStatus.REJECTED: [BugStatus.OPEN],
    BugStatus.CLOSED: [],
}


# ── Stats (before {bug_id} routes) ───────────────────

@router.get("/stats", response_model=BugStats)
async def bug_stats(
    project_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = select(Bug)
    if project_id:
        base = base.where(Bug.project_id == project_id)

    # by status
    q = select(Bug.status, func.count()).group_by(Bug.status)
    if project_id:
        q = q.where(Bug.project_id == project_id)
    rows = (await db.execute(q)).all()
    by_status = {r[0].value: r[1] for r in rows}

    # by severity
    q = select(Bug.severity, func.count()).group_by(Bug.severity)
    if project_id:
        q = q.where(Bug.project_id == project_id)
    rows = (await db.execute(q)).all()
    by_severity = {r[0].value: r[1] for r in rows}

    # 30-day trend
    since = datetime.now(timezone.utc) - timedelta(days=30)
    q = (
        select(cast(Bug.created_at, Date).label("date"), func.count())
        .where(Bug.created_at >= since)
        .group_by("date")
        .order_by("date")
    )
    if project_id:
        q = q.where(Bug.project_id == project_id)
    rows = (await db.execute(q)).all()
    trend = [{"date": str(r[0]), "count": r[1]} for r in rows]

    return BugStats(by_status=by_status, by_severity=by_severity, trend=trend)


# ── Attachment download (before {bug_id}) ─────────────

@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    att = await db.get(BugAttachment, attachment_id)
    if not att:
        raise HTTPException(404, "Attachment not found")
    return FileResponse(att.filepath, filename=att.filename)


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    att = await db.get(BugAttachment, attachment_id)
    if not att:
        raise HTTPException(404, "Attachment not found")
    if os.path.exists(att.filepath):
        os.remove(att.filepath)
    await db.delete(att)
    await db.commit()
    return {"ok": True}


# ── CRUD ──────────────────────────────────────────────

@router.get("", response_model=list[BugOut])
async def list_bugs(
    project_id: UUID | None = None,
    status: BugStatus | None = None,
    severity: BugSeverity | None = None,
    assignee_id: UUID | None = None,
    tab_node_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Bug).order_by(Bug.created_at.desc())
    if project_id:
        q = q.where(Bug.project_id == project_id)
    if status:
        q = q.where(Bug.status == status)
    if severity:
        q = q.where(Bug.severity == severity)
    if assignee_id:
        q = q.where(Bug.assignee_id == assignee_id)
    if tab_node_id:
        q = q.where(Bug.tab_node_id == tab_node_id)
    return (await db.execute(q)).scalars().all()


@router.post("", response_model=BugOut)
async def create_bug(
    body: BugCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bug = Bug(**body.model_dump(), created_by=user.id)
    db.add(bug)
    await db.commit()
    await db.refresh(bug)
    return bug


@router.get("/{bug_id}", response_model=BugOut)
async def get_bug(bug_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    bug = await db.get(Bug, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")
    return bug


@router.patch("/{bug_id}", response_model=BugOut)
async def update_bug(
    bug_id: UUID,
    body: BugUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bug = await db.get(Bug, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(bug, k, v)
    await db.commit()
    await db.refresh(bug)
    return bug


@router.delete("/{bug_id}")
async def delete_bug(bug_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    bug = await db.get(Bug, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")
    await db.delete(bug)
    await db.commit()
    return {"ok": True}


# ── Status transition ─────────────────────────────────

@router.patch("/{bug_id}/status", response_model=BugOut)
async def transition_status(
    bug_id: UUID,
    body: BugStatusTransition,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bug = await db.get(Bug, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")
    allowed = VALID_TRANSITIONS.get(bug.status, [])
    if body.status not in allowed:
        raise HTTPException(400, f"Cannot transition from {bug.status.value} to {body.status.value}")
    bug.status = body.status
    await db.commit()
    await db.refresh(bug)
    return bug


# ── Comments ──────────────────────────────────────────

@router.get("/{bug_id}/comments", response_model=list[BugCommentOut])
async def list_comments(bug_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(BugComment).where(BugComment.bug_id == bug_id).order_by(BugComment.created_at)
    return (await db.execute(q)).scalars().all()


@router.post("/{bug_id}/comments", response_model=BugCommentOut)
async def add_comment(
    bug_id: UUID,
    body: BugCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bug = await db.get(Bug, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")
    comment = BugComment(content=body.content, bug_id=bug_id, author_id=user.id)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.delete("/{bug_id}/comments/{comment_id}")
async def delete_comment(
    bug_id: UUID,
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = await db.get(BugComment, comment_id)
    if not comment or comment.bug_id != bug_id:
        raise HTTPException(404, "Comment not found")
    await db.delete(comment)
    await db.commit()
    return {"ok": True}


# ── Attachments ───────────────────────────────────────

@router.get("/{bug_id}/attachments", response_model=list[BugAttachmentOut])
async def list_attachments(bug_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(BugAttachment).where(BugAttachment.bug_id == bug_id).order_by(BugAttachment.created_at)
    return (await db.execute(q)).scalars().all()


@router.post("/{bug_id}/attachments", response_model=BugAttachmentOut)
async def upload_attachment(
    bug_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bug = await db.get(Bug, bug_id)
    if not bug:
        raise HTTPException(404, "Bug not found")
    os.makedirs(settings.BUG_UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    saved_name = f"{_uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.BUG_UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    att = BugAttachment(
        filename=file.filename or saved_name,
        filepath=filepath,
        filesize=len(content),
        bug_id=bug_id,
        uploaded_by=user.id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att

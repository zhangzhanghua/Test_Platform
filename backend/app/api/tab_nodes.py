from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, TabNode, TestCase, Bug
from app.schemas.schemas import TabNodeCreate, TabNodeUpdate, TabNodeOut

router = APIRouter(prefix="/tab-nodes", tags=["tab-nodes"])


def build_tree(nodes: list[TabNode], parent_id=None) -> list[dict]:
    result = []
    for n in nodes:
        if n.parent_id == parent_id:
            result.append({
                "id": n.id, "name": n.name, "sort_order": n.sort_order,
                "parent_id": n.parent_id,
                "children": build_tree(nodes, n.id),
            })
    result.sort(key=lambda x: x["sort_order"])
    return result


@router.get("", response_model=list[TabNodeOut])
async def list_tab_nodes(
    project_id: UUID,
    scope: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(TabNode).where(TabNode.project_id == project_id, TabNode.scope == scope).order_by(TabNode.sort_order)
    nodes = (await db.execute(q)).scalars().all()
    return build_tree(list(nodes))


@router.post("", response_model=TabNodeOut)
async def create_tab_node(
    body: TabNodeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    node = TabNode(**body.model_dump())
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


@router.patch("/{node_id}", response_model=TabNodeOut)
async def update_tab_node(
    node_id: UUID,
    body: TabNodeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    node = await db.get(TabNode, node_id)
    if not node:
        raise HTTPException(404, "Node not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(node, k, v)
    await db.commit()
    await db.refresh(node)
    return node


async def _collect_descendant_ids(db: AsyncSession, node_id: UUID) -> list[UUID]:
    ids = [node_id]
    children = (await db.execute(select(TabNode.id).where(TabNode.parent_id == node_id))).scalars().all()
    for cid in children:
        ids.extend(await _collect_descendant_ids(db, cid))
    return ids


@router.delete("/{node_id}")
async def delete_tab_node(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    node = await db.get(TabNode, node_id)
    if not node:
        raise HTTPException(404, "Node not found")
    all_ids = await _collect_descendant_ids(db, node_id)
    # Nullify references
    from sqlalchemy import update
    await db.execute(update(TestCase).where(TestCase.tab_node_id.in_(all_ids)).values(tab_node_id=None))
    await db.execute(update(Bug).where(Bug.tab_node_id.in_(all_ids)).values(tab_node_id=None))
    await db.delete(node)
    await db.commit()
    return {"ok": True}

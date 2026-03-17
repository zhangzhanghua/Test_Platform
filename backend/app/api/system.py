from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role
from app.models.models import User, SysRole, SysMenu, sys_user_role, sys_role_menu
from app.schemas.schemas import (
    SysRoleCreate, SysRoleUpdate, SysRoleOut,
    SysMenuCreate, SysMenuUpdate, SysMenuOut,
    RoleMenuAssign, UserRoleAssign, UserOut,
)

router = APIRouter(prefix="/system", tags=["system"])

_admin = require_role("admin")


# ── Roles ─────────────────────────────────────────────

@router.get("/roles", response_model=list[SysRoleOut])
async def list_roles(db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    result = await db.execute(select(SysRole).order_by(SysRole.created_at))
    return result.scalars().all()


@router.post("/roles", response_model=SysRoleOut)
async def create_role(body: SysRoleCreate, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    exists = await db.scalar(select(SysRole).where(SysRole.code == body.code))
    if exists:
        raise HTTPException(400, "Role code already exists")
    role = SysRole(**body.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.patch("/roles/{role_id}", response_model=SysRoleOut)
async def update_role(role_id: UUID, body: SysRoleUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    role = await db.get(SysRole, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(role, k, v)
    await db.commit()
    await db.refresh(role)
    return role


@router.delete("/roles/{role_id}")
async def delete_role(role_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    role = await db.get(SysRole, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    await db.delete(role)
    await db.commit()
    return {"ok": True}


# ── Role-Menu assignment ──────────────────────────────

@router.get("/roles/{role_id}/menus", response_model=list[SysMenuOut])
async def get_role_menus(role_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    role = await db.get(SysRole, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    menu_ids_q = select(sys_role_menu.c.menu_id).where(sys_role_menu.c.role_id == role_id)
    menus = (await db.execute(select(SysMenu).where(SysMenu.id.in_(menu_ids_q)).order_by(SysMenu.sort_order))).scalars().all()
    return [{"id": m.id, "name": m.name, "path": m.path, "icon": m.icon,
             "sort_order": m.sort_order, "parent_id": m.parent_id,
             "is_active": m.is_active, "children": []} for m in menus]


@router.put("/roles/{role_id}/menus")
async def set_role_menus(role_id: UUID, body: RoleMenuAssign, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    role = await db.get(SysRole, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    await db.execute(delete(sys_role_menu).where(sys_role_menu.c.role_id == role_id))
    for mid in body.menu_ids:
        await db.execute(sys_role_menu.insert().values(role_id=role_id, menu_id=mid))
    await db.commit()
    return {"ok": True}


# ── Menus ─────────────────────────────────────────────

@router.get("/menus", response_model=list[SysMenuOut])
async def list_menus(db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    all_menus = (await db.execute(select(SysMenu).order_by(SysMenu.sort_order))).scalars().all()
    menu_map = {m.id: {"id": m.id, "name": m.name, "path": m.path, "icon": m.icon,
                        "sort_order": m.sort_order, "parent_id": m.parent_id,
                        "is_active": m.is_active, "children": []} for m in all_menus}
    roots = []
    for m in all_menus:
        if m.parent_id and m.parent_id in menu_map:
            menu_map[m.parent_id]["children"].append(menu_map[m.id])
        else:
            roots.append(menu_map[m.id])
    return roots


@router.post("/menus", response_model=SysMenuOut)
async def create_menu(body: SysMenuCreate, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    menu = SysMenu(**body.model_dump())
    db.add(menu)
    await db.commit()
    await db.refresh(menu)
    return menu


@router.patch("/menus/{menu_id}", response_model=SysMenuOut)
async def update_menu(menu_id: UUID, body: SysMenuUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    menu = await db.get(SysMenu, menu_id)
    if not menu:
        raise HTTPException(404, "Menu not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(menu, k, v)
    await db.commit()
    await db.refresh(menu)
    return menu


@router.delete("/menus/{menu_id}")
async def delete_menu(menu_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    menu = await db.get(SysMenu, menu_id)
    if not menu:
        raise HTTPException(404, "Menu not found")
    await db.delete(menu)
    await db.commit()
    return {"ok": True}


# ── User-Role assignment ──────────────────────────────

@router.put("/users/{user_id}/roles", response_model=UserOut)
async def set_user_roles(user_id: UUID, body: UserRoleAssign, db: AsyncSession = Depends(get_db), _: User = Depends(_admin)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    await db.execute(delete(sys_user_role).where(sys_user_role.c.user_id == user_id))
    for rid in body.role_ids:
        await db.execute(sys_user_role.insert().values(user_id=user_id, role_id=rid))
    await db.commit()
    await db.refresh(user)
    return user

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User, SysMenu, sys_role_menu
from app.schemas.schemas import Token, LoginRequest, RegisterRequest, UserOut, UserMeOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(User).where((User.username == body.username) | (User.email == body.email)))
    if exists:
        raise HTTPException(400, "Username or email already exists")
    user = User(username=body.username, email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserMeOut)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get all menu IDs for user's roles
    role_ids = [r.id for r in user.roles]
    if not role_ids:
        return UserMeOut(
            id=user.id, username=user.username, email=user.email,
            roles=user.roles, is_active=user.is_active, created_at=user.created_at, menus=[],
        )
    menu_ids_q = select(sys_role_menu.c.menu_id).where(sys_role_menu.c.role_id.in_(role_ids)).distinct()
    all_menus = (await db.execute(
        select(SysMenu).where(SysMenu.id.in_(menu_ids_q), SysMenu.is_active == True).order_by(SysMenu.sort_order)
    )).scalars().all()
    # Build tree manually (avoid lazy-load of children)
    menu_map = {m.id: {"id": m.id, "name": m.name, "path": m.path, "icon": m.icon,
                        "sort_order": m.sort_order, "parent_id": m.parent_id,
                        "is_active": m.is_active, "children": []} for m in all_menus}
    roots = []
    for m in all_menus:
        if m.parent_id and m.parent_id in menu_map:
            menu_map[m.parent_id]["children"].append(menu_map[m.id])
        else:
            roots.append(menu_map[m.id])
    return UserMeOut(
        id=user.id, username=user.username, email=user.email,
        roles=user.roles, is_active=user.is_active, created_at=user.created_at,
        menus=roots,
    )

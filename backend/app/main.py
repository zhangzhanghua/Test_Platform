from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import engine, Base, async_session
from app.api import auth, projects, testcases, executions, environments, users, notify, webhooks, ws, bugs, system, tab_nodes


async def seed_defaults():
    """Insert default roles, menus, and role-menu mappings if tables are empty."""
    from app.models.models import SysRole, SysMenu, sys_role_menu, User, sys_user_role

    async with async_session() as db:
        existing = await db.scalar(select(SysRole.id).limit(1))
        if existing:
            return

        # ── Roles ──
        role_defs = [
            ("admin", "管理员"), ("manager", "项目经理"), ("server_dev", "服务端开发"),
            ("qa", "QA"), ("android_dev", "Android开发"), ("ios_dev", "iOS开发"),
            ("web_dev", "Web开发"), ("product", "产品"), ("ui", "UI"), ("viewer", "观察者"),
        ]
        roles = {}
        for code, name in role_defs:
            r = SysRole(code=code, name=name)
            db.add(r)
            roles[code] = r
        await db.flush()

        # ── Menus ──
        menu_defs = [
            ("仪表盘", "/", "DashboardOutlined", 0),
            ("项目管理", "/projects", "ProjectOutlined", 1),
            ("用例管理", "/testcases", "FileTextOutlined", 2),
            ("测试执行", "/executions", "PlayCircleOutlined", 3),
            ("缺陷管理", "/bugs", "BugOutlined", 4),
            ("环境管理", "/environments", "CloudServerOutlined", 5),
            ("测试报告", "/reports", "BarChartOutlined", 6),
            ("通知管理", "/notify", "BellOutlined", 7),
            ("Webhooks", "/webhooks", "ApiOutlined", 8),
            ("系统管理", "/system", "SettingOutlined", 9),
        ]
        menus = {}
        for name, path, icon, sort in menu_defs:
            m = SysMenu(name=name, path=path, icon=icon, sort_order=sort)
            db.add(m)
            menus[path] = m
        await db.flush()

        # ── Role-Menu mappings (direct insert to avoid lazy-load IO) ──
        role_menu_map = {
            "admin": list(menus.keys()),
            "manager": ["/", "/projects", "/testcases", "/executions", "/bugs", "/environments", "/reports", "/notify", "/webhooks"],
            "server_dev": ["/", "/projects", "/testcases", "/executions", "/bugs", "/reports"],
            "qa": ["/", "/projects", "/testcases", "/executions", "/bugs", "/environments", "/reports"],
            "android_dev": ["/", "/projects", "/testcases", "/executions", "/bugs", "/reports"],
            "ios_dev": ["/", "/projects", "/testcases", "/executions", "/bugs", "/reports"],
            "web_dev": ["/", "/projects", "/testcases", "/executions", "/bugs", "/reports"],
            "product": ["/", "/projects", "/bugs", "/reports"],
            "ui": ["/", "/projects", "/bugs", "/reports"],
            "viewer": ["/", "/reports"],
        }
        for code, paths in role_menu_map.items():
            for p in paths:
                await db.execute(sys_role_menu.insert().values(role_id=roles[code].id, menu_id=menus[p].id))

        # ── Migrate existing users (read old role column if it exists) ──
        old_role_map = {"admin": "admin", "manager": "manager", "tester": "qa", "viewer": "viewer"}
        try:
            from sqlalchemy import text
            rows = (await db.execute(text("SELECT id, role FROM users"))).all()
            for uid, old_role in rows:
                new_code = old_role_map.get(str(old_role).lower(), "qa")
                if new_code in roles:
                    await db.execute(sys_user_role.insert().values(user_id=uid, role_id=roles[new_code].id))
        except Exception:
            pass

        await db.commit()
        print("[seed] Default roles, menus, and mappings created.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_defaults()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(projects.router, prefix=settings.API_V1_PREFIX)
app.include_router(testcases.router, prefix=settings.API_V1_PREFIX)
app.include_router(executions.router, prefix=settings.API_V1_PREFIX)
app.include_router(environments.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(notify.router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)
app.include_router(bugs.router, prefix=settings.API_V1_PREFIX)
app.include_router(system.router, prefix=settings.API_V1_PREFIX)
app.include_router(tab_nodes.router, prefix=settings.API_V1_PREFIX)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, ForeignKey, Enum, Integer, DateTime, Boolean, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return uuid.uuid4()


# ── RBAC 关联表 ───────────────────────────────────────

sys_user_role = Table(
    "sys_user_role", Base.metadata,
    Column("user_id", PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", PG_UUID(as_uuid=True), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
)

sys_role_menu = Table(
    "sys_role_menu", Base.metadata,
    Column("role_id", PG_UUID(as_uuid=True), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_id", PG_UUID(as_uuid=True), ForeignKey("sys_menus.id", ondelete="CASCADE"), primary_key=True),
)


# ── SysRole ───────────────────────────────────────────

class SysRole(Base):
    __tablename__ = "sys_roles"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    menus: Mapped[list["SysMenu"]] = relationship(secondary=sys_role_menu, lazy="selectin")


# ── SysMenu ───────────────────────────────────────────

class SysMenu(Base):
    __tablename__ = "sys_menus"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100))
    path: Mapped[str | None] = mapped_column(String(200), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sys_menus.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    children: Mapped[list["SysMenu"]] = relationship(back_populates="parent", lazy="selectin")
    parent: Mapped["SysMenu | None"] = relationship(back_populates="children", remote_side="SysMenu.id", lazy="selectin")


# ── Enums ──────────────────────────────────────────────

class CasePriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class BugSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class BugStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"
    REJECTED = "rejected"


# ── User ───────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    roles: Mapped[list["SysRole"]] = relationship(secondary=sys_user_role, lazy="selectin")


# ── Project ────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    suites: Mapped[list["TestSuite"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    environments: Mapped[list["Environment"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    bugs: Mapped[list["Bug"]] = relationship(back_populates="project", cascade="all, delete-orphan")


# ── Environment ────────────────────────────────────────

class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(64))
    base_url: Mapped[str] = mapped_column(String(256), default="")
    variables: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    project: Mapped["Project"] = relationship(back_populates="environments")


# ── TestSuite ──────────────────────────────────────────

class TestSuite(Base):
    __tablename__ = "test_suites"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship(back_populates="suites")
    cases: Mapped[list["TestCase"]] = relationship(back_populates="suite", cascade="all, delete-orphan")


# ── TestCase ───────────────────────────────────────────

class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[CasePriority] = mapped_column(Enum(CasePriority), default=CasePriority.P1)
    tags: Mapped[str] = mapped_column(String(512), default="")  # comma-separated
    script_path: Mapped[str] = mapped_column(String(512), default="")
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_suites.id"))
    tab_node_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tab_nodes.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    suite: Mapped["TestSuite"] = relationship(back_populates="cases")
    results: Mapped[list["TestResult"]] = relationship(back_populates="case", cascade="all, delete-orphan")


# ── TestExecution (一次执行批次) ────────────────────────

class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(256))
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    trigger_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    environment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("environments.id"), nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    results: Mapped[list["TestResult"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


# ── TestResult (单条用例结果) ──────────────────────────

class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_executions.id"))
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_cases.id"))
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    log: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    execution: Mapped["TestExecution"] = relationship(back_populates="results")
    case: Mapped["TestCase"] = relationship(back_populates="results")


# ── NotifyChannel (通知渠道配置) ───────────────────────

class NotifyType(str, enum.Enum):
    EMAIL = "email"
    FEISHU = "feishu"


class NotifyChannel(Base):
    __tablename__ = "notify_channels"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128))
    channel_type: Mapped[NotifyType] = mapped_column(Enum(NotifyType))
    config: Mapped[str] = mapped_column(Text, default="{}")  # JSON: email→{"recipients":"a@b.com,c@d.com"}, feishu→{"webhook_url":"..."}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ── Webhook (CI/CD 触发) ──────────────────────────────

def gen_token():
    return uuid.uuid4().hex


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=gen_token)
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_suites.id"))
    environment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("environments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ── Bug ───────────────────────────────────────────────

class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[BugSeverity] = mapped_column(Enum(BugSeverity), default=BugSeverity.MINOR)
    status: Mapped[BugStatus] = mapped_column(Enum(BugStatus), default=BugStatus.OPEN)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    test_case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("test_cases.id"), nullable=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    tab_node_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tab_nodes.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project: Mapped["Project"] = relationship(back_populates="bugs")
    comments: Mapped[list["BugComment"]] = relationship(back_populates="bug", cascade="all, delete-orphan")
    attachments: Mapped[list["BugAttachment"]] = relationship(back_populates="bug", cascade="all, delete-orphan")


class BugComment(Base):
    __tablename__ = "bug_comments"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    content: Mapped[str] = mapped_column(Text)
    bug_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bugs.id"))
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bug: Mapped["Bug"] = relationship(back_populates="comments")


class BugAttachment(Base):
    __tablename__ = "bug_attachments"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    filename: Mapped[str] = mapped_column(String(256))
    filepath: Mapped[str] = mapped_column(String(512))
    filesize: Mapped[int] = mapped_column(Integer)
    bug_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bugs.id"))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bug: Mapped["Bug"] = relationship(back_populates="attachments")


# ── TabNode (分类树节点) ─────────────────────────────

class TabNode(Base):
    __tablename__ = "tab_nodes"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100))
    scope: Mapped[str] = mapped_column(String(20))  # "testcase" | "bug"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tab_nodes.id", ondelete="CASCADE"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    children: Mapped[list["TabNode"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped["TabNode | None"] = relationship(back_populates="children", remote_side="TabNode.id")
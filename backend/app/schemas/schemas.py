from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.models import CasePriority, ExecutionStatus, NotifyType, BugSeverity, BugStatus


# ── RBAC ──────────────────────────────────────────────

class SysRoleOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class SysRoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class SysRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SysMenuOut(BaseModel):
    id: UUID
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    parent_id: Optional[UUID] = None
    is_active: bool
    children: list["SysMenuOut"] = []
    model_config = {"from_attributes": True}


class SysMenuCreate(BaseModel):
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    parent_id: Optional[UUID] = None


class SysMenuUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class RoleMenuAssign(BaseModel):
    menu_ids: list[UUID]


class UserRoleAssign(BaseModel):
    role_ids: list[UUID]


# ── Auth ───────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class UserOut(BaseModel):
    id: UUID
    username: str
    email: str
    roles: list[SysRoleOut] = []
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMeOut(UserOut):
    menus: list[SysMenuOut] = []


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None


# ── Project ────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Environment ────────────────────────────────────────

class EnvironmentCreate(BaseModel):
    name: str
    base_url: str = ""
    variables: str = "{}"
    project_id: UUID


class EnvironmentOut(BaseModel):
    id: UUID
    name: str
    base_url: str
    variables: str
    project_id: UUID

    model_config = {"from_attributes": True}


# ── TestSuite ──────────────────────────────────────────

class TestSuiteCreate(BaseModel):
    name: str
    description: str = ""
    project_id: UUID


class TestSuiteOut(BaseModel):
    id: UUID
    name: str
    description: str
    project_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── TestCase ───────────────────────────────────────────

class TestCaseCreate(BaseModel):
    title: str
    description: str = ""
    priority: CasePriority = CasePriority.P1
    tags: str = ""
    script_path: str = ""
    suite_id: UUID
    tab_node_id: Optional[UUID] = None


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[CasePriority] = None
    tags: Optional[str] = None
    script_path: Optional[str] = None


class TestCaseOut(BaseModel):
    id: UUID
    title: str
    description: str
    priority: CasePriority
    tags: str
    script_path: str
    suite_id: UUID
    tab_node_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── TestExecution ──────────────────────────────────────

class ExecutionCreate(BaseModel):
    name: str
    case_ids: list[UUID]
    environment_id: Optional[UUID] = None


class ExecutionOut(BaseModel):
    id: UUID
    name: str
    status: ExecutionStatus
    total: int
    passed: int
    failed: int
    duration_ms: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── TestResult ─────────────────────────────────────────

class TestResultOut(BaseModel):
    id: UUID
    execution_id: UUID
    case_id: UUID
    status: ExecutionStatus
    duration_ms: int
    log: str
    error_message: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── NotifyChannel ──────────────────────────────────────

class NotifyChannelCreate(BaseModel):
    name: str
    channel_type: NotifyType
    config: str = "{}"
    is_active: bool = True
    project_id: Optional[UUID] = None


class NotifyChannelUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[str] = None
    is_active: Optional[bool] = None


class NotifyChannelOut(BaseModel):
    id: UUID
    name: str
    channel_type: NotifyType
    config: str
    is_active: bool
    project_id: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Webhook ────────────────────────────────────────────

class WebhookCreate(BaseModel):
    name: str
    suite_id: UUID
    environment_id: Optional[UUID] = None


class WebhookOut(BaseModel):
    id: UUID
    name: str
    token: str
    suite_id: UUID
    environment_id: Optional[UUID]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookTriggerResponse(BaseModel):
    execution_id: UUID
    message: str


# ── Bug ───────────────────────────────────────────────

class BugCreate(BaseModel):
    title: str
    description: str = ""
    severity: BugSeverity = BugSeverity.MINOR
    project_id: UUID
    test_case_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    tab_node_id: Optional[UUID] = None


class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[BugSeverity] = None
    assignee_id: Optional[UUID] = None
    test_case_id: Optional[UUID] = None


class BugOut(BaseModel):
    id: UUID
    title: str
    description: str
    severity: BugSeverity
    status: BugStatus
    project_id: UUID
    test_case_id: Optional[UUID]
    assignee_id: Optional[UUID]
    created_by: UUID
    tab_node_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BugStatusTransition(BaseModel):
    status: BugStatus


class BugCommentCreate(BaseModel):
    content: str


class BugCommentOut(BaseModel):
    id: UUID
    content: str
    bug_id: UUID
    author_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class BugAttachmentOut(BaseModel):
    id: UUID
    filename: str
    filesize: int
    bug_id: UUID
    uploaded_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class BugStats(BaseModel):
    by_status: dict[str, int]
    by_severity: dict[str, int]
    trend: list[dict]


# ── TabNode ──────────────────────────────────────────

class TabNodeCreate(BaseModel):
    name: str
    scope: str
    project_id: UUID
    parent_id: Optional[UUID] = None


class TabNodeUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


class TabNodeOut(BaseModel):
    id: UUID
    name: str
    sort_order: int
    parent_id: Optional[UUID] = None
    children: list["TabNodeOut"] = []

    model_config = {"from_attributes": True}

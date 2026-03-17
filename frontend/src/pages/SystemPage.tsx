import React, { useEffect, useState } from 'react';
import { Tabs, Table, Button, Modal, Form, Input, Select, Switch, Tree, Popconfirm, message, Tag, Space } from 'antd';
import api from '@/services/api';

// ── 用户管理 Tab ──────────────────────────────────────

const UsersTab: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);

  const load = () => {
    api.get('/users').then(r => setUsers(r.data)).catch(() => message.error('无权限'));
    api.get('/system/roles').then(r => setRoles(r.data));
    api.get('/auth/me').then(r => setCurrentUser(r.data));
  };
  useEffect(() => { load(); }, []);

  const saveRoles = async () => {
    await api.put(`/system/users/${editingUser.id}/roles`, { role_ids: selectedRoleIds });
    message.success('角色已更新');
    setEditingUser(null);
    load();
  };

  const toggleActive = async (id: string, checked: boolean) => {
    await api.patch(`/users/${id}`, { is_active: checked });
    message.success('已更新');
    load();
  };

  const deleteUser = async (id: string) => {
    await api.delete(`/users/${id}`);
    message.success('已删除');
    load();
  };

  return (
    <>
      <Table rowKey="id" dataSource={users} columns={[
        { title: '用户名', dataIndex: 'username' },
        { title: '邮箱', dataIndex: 'email' },
        {
          title: '角色', dataIndex: 'roles',
          render: (roles: any[]) => roles?.map(r => <Tag key={r.id} color="blue">{r.name}</Tag>),
        },
        {
          title: '状态', dataIndex: 'is_active',
          render: (v: boolean, rec: any) => (
            <Switch checked={v} checkedChildren="启用" unCheckedChildren="禁用"
              onChange={c => toggleActive(rec.id, c)} />
          ),
        },
        { title: '注册时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
        {
          title: '操作',
          render: (_: any, rec: any) => (
            <Space>
              <a onClick={() => { setEditingUser(rec); setSelectedRoleIds(rec.roles?.map((r: any) => r.id) || []); }}>编辑角色</a>
              {currentUser?.id !== rec.id && (
                <Popconfirm title="确认删除？" onConfirm={() => deleteUser(rec.id)}>
                  <a style={{ color: 'red' }}>删除</a>
                </Popconfirm>
              )}
            </Space>
          ),
        },
      ]} />
      <Modal title="编辑用户角色" open={!!editingUser} onOk={saveRoles} onCancel={() => setEditingUser(null)}>
        <Select mode="multiple" style={{ width: '100%' }} value={selectedRoleIds}
          onChange={setSelectedRoleIds}
          options={roles.map(r => ({ label: r.name, value: r.id }))} />
      </Modal>
    </>
  );
};

// ── 角色管理 Tab ──────────────────────────────────────

const RolesTab: React.FC = () => {
  const [roles, setRoles] = useState<any[]>([]);
  const [menus, setMenus] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [menuModalRole, setMenuModalRole] = useState<any>(null);
  const [checkedMenuIds, setCheckedMenuIds] = useState<string[]>([]);
  const [form] = Form.useForm();

  const load = () => {
    api.get('/system/roles').then(r => setRoles(r.data));
    api.get('/system/menus').then(r => setMenus(r.data));
  };
  useEffect(() => { load(); }, []);

  const flatMenuIds = (items: any[]): string[] =>
    items.flatMap(m => [m.id, ...flatMenuIds(m.children || [])]);

  const menuTreeData = (items: any[]): any[] =>
    items.map(m => ({ title: m.name, key: m.id, children: menuTreeData(m.children || []) }));

  const saveRole = async (values: any) => {
    await api.post('/system/roles', values);
    message.success('创建成功');
    setModalOpen(false);
    form.resetFields();
    load();
  };

  const deleteRole = async (id: string) => {
    await api.delete(`/system/roles/${id}`);
    message.success('已删除');
    load();
  };

  const openMenuModal = async (role: any) => {
    const res = await api.get(`/system/roles/${role.id}/menus`);
    setCheckedMenuIds(flatMenuIds(res.data).length ? res.data.map((m: any) => m.id) : []);
    setMenuModalRole(role);
  };

  const saveMenus = async () => {
    await api.put(`/system/roles/${menuModalRole.id}/menus`, { menu_ids: checkedMenuIds });
    message.success('菜单已更新');
    setMenuModalRole(null);
    load();
  };

  return (
    <>
      <Button type="primary" style={{ marginBottom: 16 }} onClick={() => setModalOpen(true)}>新增角色</Button>
      <Table rowKey="id" dataSource={roles} columns={[
        { title: '编码', dataIndex: 'code' },
        { title: '名称', dataIndex: 'name' },
        { title: '描述', dataIndex: 'description' },
        {
          title: '操作',
          render: (_: any, rec: any) => (
            <Space>
              <a onClick={() => openMenuModal(rec)}>配置菜单</a>
              <Popconfirm title="确认删除？" onConfirm={() => deleteRole(rec.id)}>
                <a style={{ color: 'red' }}>删除</a>
              </Popconfirm>
            </Space>
          ),
        },
      ]} />
      <Modal title="新增角色" open={modalOpen} onOk={() => form.submit()} onCancel={() => setModalOpen(false)}>
        <Form form={form} onFinish={saveRole} layout="vertical">
          <Form.Item name="code" label="编码" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea /></Form.Item>
        </Form>
      </Modal>
      <Modal title={`配置菜单 - ${menuModalRole?.name}`} open={!!menuModalRole}
        onOk={saveMenus} onCancel={() => setMenuModalRole(null)}>
        <Tree checkable checkedKeys={checkedMenuIds}
          onCheck={(keys) => setCheckedMenuIds(keys as string[])}
          treeData={menuTreeData(menus)} />
      </Modal>
    </>
  );
};

// ── 菜单管理 Tab ──────────────────────────────────────

const iconOptions = [
  'DashboardOutlined', 'ProjectOutlined', 'FileTextOutlined', 'PlayCircleOutlined',
  'BarChartOutlined', 'CloudServerOutlined', 'BellOutlined', 'ApiOutlined',
  'TeamOutlined', 'SettingOutlined', 'BugOutlined',
].map(v => ({ label: v, value: v }));

const MenusTab: React.FC = () => {
  const [menus, setMenus] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();

  const load = () => api.get('/system/menus').then(r => setMenus(r.data));
  useEffect(() => { load(); }, []);

  const flatMenus = (items: any[], depth = 0): any[] =>
    items.flatMap(m => [{ ...m, _depth: depth }, ...flatMenus(m.children || [], depth + 1)]);

  const allFlat = flatMenus(menus);

  const save = async (values: any) => {
    if (editing) {
      await api.patch(`/system/menus/${editing.id}`, values);
      message.success('已更新');
    } else {
      await api.post('/system/menus', values);
      message.success('创建成功');
    }
    setModalOpen(false);
    setEditing(null);
    form.resetFields();
    load();
  };

  const deleteMenu = async (id: string) => {
    await api.delete(`/system/menus/${id}`);
    message.success('已删除');
    load();
  };

  const openEdit = (rec: any) => {
    setEditing(rec);
    form.setFieldsValue(rec);
    setModalOpen(true);
  };

  return (
    <>
      <Button type="primary" style={{ marginBottom: 16 }} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>新增菜单</Button>
      <Table rowKey="id" dataSource={allFlat} pagination={false} columns={[
        { title: '名称', dataIndex: 'name', render: (v: string, r: any) => <span style={{ paddingLeft: r._depth * 24 }}>{v}</span> },
        { title: '路径', dataIndex: 'path' },
        { title: '图标', dataIndex: 'icon' },
        { title: '排序', dataIndex: 'sort_order' },
        {
          title: '操作',
          render: (_: any, rec: any) => (
            <Space>
              <a onClick={() => openEdit(rec)}>编辑</a>
              <Popconfirm title="确认删除？" onConfirm={() => deleteMenu(rec.id)}>
                <a style={{ color: 'red' }}>删除</a>
              </Popconfirm>
            </Space>
          ),
        },
      ]} />
      <Modal title={editing ? '编辑菜单' : '新增菜单'} open={modalOpen}
        onOk={() => form.submit()} onCancel={() => { setModalOpen(false); setEditing(null); }}>
        <Form form={form} onFinish={save} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="path" label="路径"><Input /></Form.Item>
          <Form.Item name="icon" label="图标"><Select options={iconOptions} allowClear /></Form.Item>
          <Form.Item name="sort_order" label="排序"><Input type="number" /></Form.Item>
          <Form.Item name="parent_id" label="父菜单">
            <Select allowClear options={allFlat.map(m => ({ label: m.name, value: m.id }))} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

// ── Main Page ─────────────────────────────────────────

const SystemPage: React.FC = () => (
  <Tabs items={[
    { key: 'users', label: '用户管理', children: <UsersTab /> },
    { key: 'roles', label: '角色管理', children: <RolesTab /> },
    { key: 'menus', label: '菜单管理', children: <MenusTab /> },
  ]} />
);

export default SystemPage;

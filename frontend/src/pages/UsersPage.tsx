import React, { useEffect, useState } from 'react';
import { Table, Tag, Select, Switch, Popconfirm, message } from 'antd';
import api from '@/services/api';

const roleColors: Record<string, string> = { admin: 'red', manager: 'orange', tester: 'blue', viewer: 'default' };

const UsersPage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [currentUser, setCurrentUser] = useState<any>(null);

  const load = () => {
    api.get('/users').then((r) => setData(r.data)).catch(() => message.error('无权限访问'));
    api.get('/auth/me').then((r) => setCurrentUser(r.data));
  };
  useEffect(() => { load(); }, []);

  const updateUser = async (id: string, patch: any) => {
    await api.patch(`/users/${id}`, patch);
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
      <h3>用户管理</h3>
      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '用户名', dataIndex: 'username' },
          { title: '邮箱', dataIndex: 'email' },
          {
            title: '角色', dataIndex: 'role',
            render: (v: string, record: any) => (
              <Select
                value={v}
                style={{ width: 120 }}
                onChange={(role) => updateUser(record.id, { role })}
                options={['admin', 'manager', 'tester', 'viewer'].map((r) => ({ label: <Tag color={roleColors[r]}>{r.toUpperCase()}</Tag>, value: r }))}
              />
            ),
          },
          {
            title: '状态', dataIndex: 'is_active',
            render: (v: boolean, record: any) => (
              <Switch checked={v} checkedChildren="启用" unCheckedChildren="禁用"
                onChange={(checked) => updateUser(record.id, { is_active: checked })} />
            ),
          },
          { title: '注册时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
          {
            title: '操作',
            render: (_: any, record: any) =>
              currentUser?.id !== record.id ? (
                <Popconfirm title="确认删除？" onConfirm={() => deleteUser(record.id)}>
                  <a style={{ color: 'red' }}>删除</a>
                </Popconfirm>
              ) : <Tag>当前用户</Tag>,
          },
        ]}
      />
    </>
  );
};

export default UsersPage;

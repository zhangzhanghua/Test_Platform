import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Switch, Space, Tag, message, Popconfirm, Tabs } from 'antd';
import { PlusOutlined, SendOutlined } from '@ant-design/icons';
import api from '@/services/api';

const typeLabels: Record<string, { label: string; color: string }> = {
  email: { label: '邮件', color: 'blue' },
  feishu: { label: '飞书', color: 'green' },
};

const NotifyPage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();
  const [channelType, setChannelType] = useState<string>('email');

  const load = () => api.get('/notify-channels').then((r) => setData(r.data));
  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setChannelType('email');
    setOpen(true);
  };

  const openEdit = (record: any) => {
    setEditing(record);
    setChannelType(record.channel_type);
    const cfg = JSON.parse(record.config || '{}');
    form.setFieldsValue({ name: record.name, channel_type: record.channel_type, ...cfg });
    setOpen(true);
  };

  const onSubmit = async () => {
    const values = await form.validateFields();
    const { name, channel_type, ...rest } = values;
    const config = JSON.stringify(rest);
    if (editing) {
      await api.patch(`/notify-channels/${editing.id}`, { name, config });
    } else {
      await api.post('/notify-channels', { name, channel_type, config });
    }
    message.success(editing ? '已更新' : '创建成功');
    setOpen(false);
    load();
  };

  const onDelete = async (id: string) => {
    await api.delete(`/notify-channels/${id}`);
    message.success('已删除');
    load();
  };

  const onToggle = async (id: string, checked: boolean) => {
    await api.patch(`/notify-channels/${id}`, { is_active: checked });
    load();
  };

  const onTest = async (id: string) => {
    await api.post(`/notify-channels/${id}/test`);
    message.success('测试通知已发送');
  };

  return (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3>通知管理</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建通知渠道</Button>
      </div>

      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '名称', dataIndex: 'name' },
          {
            title: '类型', dataIndex: 'channel_type',
            render: (v: string) => <Tag color={typeLabels[v]?.color}>{typeLabels[v]?.label || v}</Tag>,
          },
          {
            title: '配置摘要', dataIndex: 'config',
            render: (v: string, record: any) => {
              const cfg = JSON.parse(v || '{}');
              if (record.channel_type === 'email') return cfg.recipients || '-';
              if (record.channel_type === 'feishu') return cfg.webhook_url ? '已配置 Webhook' : '-';
              return '-';
            },
          },
          {
            title: '状态', dataIndex: 'is_active',
            render: (v: boolean, record: any) => (
              <Switch checked={v} checkedChildren="启用" unCheckedChildren="禁用" onChange={(c) => onToggle(record.id, c)} />
            ),
          },
          { title: '创建时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
          {
            title: '操作',
            render: (_: any, record: any) => (
              <Space>
                <a onClick={() => openEdit(record)}>编辑</a>
                <a onClick={() => onTest(record.id)}><SendOutlined /> 测试</a>
                <Popconfirm title="确认删除？" onConfirm={() => onDelete(record.id)}>
                  <a style={{ color: 'red' }}>删除</a>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal title={editing ? '编辑通知渠道' : '新建通知渠道'} open={open} onOk={onSubmit} onCancel={() => setOpen(false)} width={560}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="渠道名称" rules={[{ required: true }]}>
            <Input placeholder="如: 项目A邮件通知" />
          </Form.Item>
          {!editing && (
            <Form.Item name="channel_type" label="通知类型" initialValue="email" rules={[{ required: true }]}>
              <Select onChange={(v) => setChannelType(v)} options={[
                { label: '📧 邮件', value: 'email' },
                { label: '💬 飞书', value: 'feishu' },
              ]} />
            </Form.Item>
          )}

          {channelType === 'email' && (
            <Form.Item name="recipients" label="收件人" rules={[{ required: true }]}
              extra="多个邮箱用逗号分隔">
              <Input.TextArea rows={2} placeholder="user1@example.com, user2@example.com" />
            </Form.Item>
          )}

          {channelType === 'feishu' && (
            <Form.Item name="webhook_url" label="飞书 Webhook URL" rules={[{ required: true }]}
              extra="在飞书群设置 → 群机器人 → 自定义机器人中获取">
              <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  );
};

export default NotifyPage;

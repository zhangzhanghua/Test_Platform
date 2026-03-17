import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Switch, Space, Tag, message, Popconfirm, Typography } from 'antd';
import { PlusOutlined, CopyOutlined, ApiOutlined } from '@ant-design/icons';
import api from '@/services/api';

const { Text } = Typography;

const WebhooksPage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [suites, setSuites] = useState<any[]>([]);
  const [environments, setEnvironments] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>();
  const [form] = Form.useForm();

  const load = () => api.get('/webhooks').then((r) => setData(r.data));
  useEffect(() => {
    load();
    api.get('/projects').then((r) => setProjects(r.data));
  }, []);

  const onProjectChange = (pid: string) => {
    setSelectedProject(pid);
    api.get('/testcases/suites', { params: { project_id: pid } }).then((r) => setSuites(r.data));
    api.get('/environments', { params: { project_id: pid } }).then((r) => setEnvironments(r.data));
  };

  const onSubmit = async () => {
    const values = await form.validateFields();
    await api.post('/webhooks', { name: values.name, suite_id: values.suite_id, environment_id: values.environment_id || null });
    message.success('创建成功');
    setOpen(false);
    form.resetFields();
    load();
  };

  const onToggle = async (id: string, checked: boolean) => {
    await api.patch(`/webhooks/${id}`, null, { params: { is_active: checked } });
    load();
  };

  const onDelete = async (id: string) => {
    await api.delete(`/webhooks/${id}`);
    message.success('已删除');
    load();
  };

  const copyUrl = (token: string) => {
    const url = `${window.location.origin}/api/v1/webhooks/${token}/trigger`;
    navigator.clipboard.writeText(url);
    message.success('Webhook URL 已复制');
  };

  const copyCurl = (token: string) => {
    const url = `${window.location.origin}/api/v1/webhooks/${token}/trigger`;
    const cmd = `curl -X POST ${url} -H "Content-Type: application/json" -d '{"name": "CI Build #123"}'`;
    navigator.clipboard.writeText(cmd);
    message.success('cURL 命令已复制');
  };

  return (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3>Webhook 管理</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>新建 Webhook</Button>
      </div>

      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '名称', dataIndex: 'name' },
          {
            title: 'Token', dataIndex: 'token',
            render: (v: string) => <Text code copyable>{v}</Text>,
          },
          {
            title: 'Trigger URL', dataIndex: 'token',
            key: 'url',
            render: (v: string) => (
              <Space>
                <a onClick={() => copyUrl(v)}><CopyOutlined /> 复制 URL</a>
                <a onClick={() => copyCurl(v)}><ApiOutlined /> 复制 cURL</a>
              </Space>
            ),
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
              <Popconfirm title="确认删除？" onConfirm={() => onDelete(record.id)}>
                <a style={{ color: 'red' }}>删除</a>
              </Popconfirm>
            ),
          },
        ]}
      />

      <Modal title="新建 Webhook" open={open} onOk={onSubmit} onCancel={() => { setOpen(false); form.resetFields(); }} width={520}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Webhook 名称" rules={[{ required: true }]}>
            <Input placeholder="如: CI 回归测试触发器" />
          </Form.Item>
          <Form.Item label="选择项目" required>
            <Select placeholder="选择项目" onChange={onProjectChange}
              options={projects.map((p: any) => ({ label: p.name, value: p.id }))} />
          </Form.Item>
          <Form.Item name="suite_id" label="绑定测试套件" rules={[{ required: true }]}>
            <Select placeholder="选择套件" options={suites.map((s: any) => ({ label: s.name, value: s.id }))} />
          </Form.Item>
          <Form.Item name="environment_id" label="执行环境（可选）">
            <Select allowClear placeholder="选择环境" options={environments.map((e: any) => ({ label: e.name, value: e.id }))} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default WebhooksPage;

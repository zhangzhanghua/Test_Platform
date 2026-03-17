import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Popconfirm, Space, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '@/services/api';

const EnvironmentsPage: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>();
  const [data, setData] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();

  useEffect(() => { api.get('/projects').then((r) => setProjects(r.data)); }, []);

  const load = (pid: string) => api.get('/environments', { params: { project_id: pid } }).then((r) => setData(r.data));

  useEffect(() => { if (selectedProject) load(selectedProject); }, [selectedProject]);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setOpen(true);
  };

  const openEdit = (record: any) => {
    setEditing(record);
    form.setFieldsValue({
      name: record.name,
      base_url: record.base_url,
      variables: record.variables,
    });
    setOpen(true);
  };

  const onSubmit = async () => {
    const values = await form.validateFields();
    if (editing) {
      await api.put(`/environments/${editing.id}`, { ...values, project_id: selectedProject });
      message.success('更新成功');
    } else {
      await api.post('/environments', { ...values, project_id: selectedProject });
      message.success('创建成功');
    }
    setOpen(false);
    form.resetFields();
    load(selectedProject!);
  };

  const onDelete = async (id: string) => {
    await api.delete(`/environments/${id}`);
    message.success('已删除');
    load(selectedProject!);
  };

  const parseVars = (json: string) => {
    try { return Object.entries(JSON.parse(json)); } catch { return []; }
  };

  return (
    <>
      <h3>环境管理</h3>
      <Space style={{ marginBottom: 16 }}>
        <Select placeholder="选择项目" style={{ width: 200 }} onChange={(v) => setSelectedProject(v)}
          options={projects.map((p: any) => ({ label: p.name, value: p.id }))} />
        <Button type="primary" icon={<PlusOutlined />} disabled={!selectedProject} onClick={openCreate}>新建环境</Button>
      </Space>

      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '环境名称', dataIndex: 'name' },
          { title: 'Base URL', dataIndex: 'base_url' },
          {
            title: '环境变量', dataIndex: 'variables',
            render: (v: string) => (
              <Space wrap>
                {parseVars(v).map(([k, val]) => <Tag key={k as string}>{`${k}=${val}`}</Tag>)}
              </Space>
            ),
          },
          {
            title: '操作',
            render: (_: any, record: any) => (
              <Space>
                <a onClick={() => openEdit(record)}>编辑</a>
                <Popconfirm title="确认删除？" onConfirm={() => onDelete(record.id)}>
                  <a style={{ color: 'red' }}>删除</a>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal title={editing ? '编辑环境' : '新建环境'} open={open} onOk={onSubmit} onCancel={() => setOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="环境名称" rules={[{ required: true }]}><Input placeholder="如: dev / staging / prod" /></Form.Item>
          <Form.Item name="base_url" label="Base URL"><Input placeholder="https://api.example.com" /></Form.Item>
          <Form.Item name="variables" label="环境变量 (JSON)" initialValue="{}">
            <Input.TextArea rows={4} placeholder='{"DB_HOST": "localhost", "DEBUG": "true"}' />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default EnvironmentsPage;

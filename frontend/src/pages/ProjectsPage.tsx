import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, message, Popconfirm, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '@/services/api';

const ProjectsPage: React.FC = () => {
  const [data, setData] = useState([]);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const load = () => api.get('/projects').then((r) => setData(r.data));
  useEffect(() => { load(); }, []);

  const onSubmit = async () => {
    const values = await form.validateFields();
    await api.post('/projects', values);
    message.success('创建成功');
    setOpen(false);
    form.resetFields();
    load();
  };

  const onDelete = async (id: string) => {
    await api.delete(`/projects/${id}`);
    message.success('已删除');
    load();
  };

  return (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3>项目管理</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>新建项目</Button>
      </div>
      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '项目名称', dataIndex: 'name' },
          { title: '描述', dataIndex: 'description' },
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
      <Modal title="新建项目" open={open} onOk={onSubmit} onCancel={() => setOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea /></Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default ProjectsPage;

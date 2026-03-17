import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Table, Button, Modal, Form, Input, Select, Tag, message, Popconfirm, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '@/services/api';

const priorityColors: Record<string, string> = { P0: 'red', P1: 'orange', P2: 'blue', P3: 'default' };

const TestCasesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const selectedProject = searchParams.get('project_id') || undefined;
  const selectedNode = searchParams.get('tab_node_id') || null;

  const [suites, setSuites] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<string>();
  const [caseModal, setCaseModal] = useState(false);
  const [suiteModal, setSuiteModal] = useState(false);
  const [caseForm] = Form.useForm();
  const [suiteForm] = Form.useForm();

  useEffect(() => {
    if (selectedProject) {
      api.get('/testcases/suites', { params: { project_id: selectedProject } }).then((r) => setSuites(r.data));
      setSelectedSuite(undefined);
      setCases([]);
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedSuite) {
      const params: any = { suite_id: selectedSuite };
      if (selectedNode) params.tab_node_id = selectedNode;
      api.get('/testcases/cases', { params }).then((r) => setCases(r.data));
    }
  }, [selectedSuite, selectedNode]);

  const createSuite = async () => {
    const values = await suiteForm.validateFields();
    await api.post('/testcases/suites', { ...values, project_id: selectedProject });
    message.success('创建成功');
    setSuiteModal(false);
    suiteForm.resetFields();
    api.get('/testcases/suites', { params: { project_id: selectedProject } }).then((r) => setSuites(r.data));
  };

  const createCase = async () => {
    const values = await caseForm.validateFields();
    await api.post('/testcases/cases', { ...values, suite_id: selectedSuite, tab_node_id: selectedNode || undefined });
    message.success('创建成功');
    setCaseModal(false);
    caseForm.resetFields();
    const params: any = { suite_id: selectedSuite };
    if (selectedNode) params.tab_node_id = selectedNode;
    api.get('/testcases/cases', { params }).then((r) => setCases(r.data));
  };

  const deleteCase = async (id: string) => {
    await api.delete(`/testcases/cases/${id}`);
    message.success('已删除');
    const params: any = { suite_id: selectedSuite };
    if (selectedNode) params.tab_node_id = selectedNode;
    api.get('/testcases/cases', { params }).then((r) => setCases(r.data));
  };

  if (!selectedProject) return <div style={{ color: '#999', textAlign: 'center', marginTop: 80 }}>请在左侧选择项目</div>;

  return (
    <>
      <h3>用例管理</h3>
      <Space style={{ marginBottom: 16 }}>
        <Select placeholder="选择套件" style={{ width: 200 }} onChange={setSelectedSuite} value={selectedSuite}
          options={suites.map((s: any) => ({ label: s.name, value: s.id }))} />
        <Button onClick={() => setSuiteModal(true)}>新建套件</Button>
        <Button type="primary" icon={<PlusOutlined />} disabled={!selectedSuite} onClick={() => setCaseModal(true)}>新建用例</Button>
      </Space>

      <Table
        rowKey="id"
        dataSource={cases}
        columns={[
          { title: '标题', dataIndex: 'title' },
          { title: '优先级', dataIndex: 'priority', render: (v: string) => <Tag color={priorityColors[v]}>{v}</Tag> },
          { title: '标签', dataIndex: 'tags' },
          { title: '脚本路径', dataIndex: 'script_path' },
          {
            title: '操作',
            render: (_: any, r: any) => (
              <Popconfirm title="确认删除？" onConfirm={() => deleteCase(r.id)}>
                <a style={{ color: 'red' }}>删除</a>
              </Popconfirm>
            ),
          },
        ]}
      />

      <Modal title="新建套件" open={suiteModal} onOk={createSuite} onCancel={() => setSuiteModal(false)}>
        <Form form={suiteForm} layout="vertical">
          <Form.Item name="name" label="套件名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea /></Form.Item>
        </Form>
      </Modal>

      <Modal title="新建用例" open={caseModal} onOk={createCase} onCancel={() => setCaseModal(false)}>
        <Form form={caseForm} layout="vertical">
          <Form.Item name="title" label="用例标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea /></Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="P1">
            <Select options={['P0', 'P1', 'P2', 'P3'].map((p) => ({ label: p, value: p }))} />
          </Form.Item>
          <Form.Item name="tags" label="标签"><Input placeholder="逗号分隔" /></Form.Item>
          <Form.Item name="script_path" label="脚本路径"><Input /></Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default TestCasesPage;

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Table, Button, Modal, Form, Input, Select, Tag, message, Popconfirm, Space, Row, Col, Card, Upload, List } from 'antd';
import { PlusOutlined, UploadOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import api from '@/services/api';

const severityColors: Record<string, string> = { critical: 'red', major: 'orange', minor: 'blue', trivial: 'default' };
const statusColors: Record<string, string> = { open: 'red', in_progress: 'processing', fixed: 'cyan', verified: 'green', closed: 'default', rejected: 'default' };
const statusLabels: Record<string, string> = { open: '待处理', in_progress: '处理中', fixed: '已修复', verified: '已验证', closed: '已关闭', rejected: '已拒绝' };
const severityLabels: Record<string, string> = { critical: '严重', major: '主要', minor: '次要', trivial: '轻微' };

const TRANSITIONS: Record<string, string[]> = {
  open: ['in_progress', 'rejected'],
  in_progress: ['fixed', 'open'],
  fixed: ['verified', 'in_progress'],
  verified: ['closed', 'in_progress'],
  rejected: ['open'],
};

const EditableCell: React.FC<{
  value: string; onSave: (v: string) => void; type?: 'input' | 'select';
  options?: { label: string; value: string }[]; render?: React.ReactNode;
}> = ({ value, onSave, type = 'input', options, render }) => {
  const [editing, setEditing] = useState(false);
  if (!editing) return <div style={{ cursor: 'pointer' }} onClick={() => setEditing(true)}>{render || value}</div>;
  if (type === 'select') return (
    <Select size="small" autoFocus defaultOpen defaultValue={value} style={{ width: '100%' }}
      options={options} onChange={(v) => { onSave(v); setEditing(false); }}
      onBlur={() => setEditing(false)} />
  );
  return <Input size="small" autoFocus defaultValue={value}
    onPressEnter={(e) => { onSave((e.target as HTMLInputElement).value); setEditing(false); }}
    onBlur={(e) => { if (e.target.value !== value) onSave(e.target.value); setEditing(false); }} />;
};

const BugsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') || undefined;
  const selectedNode = searchParams.get('tab_node_id') || null;

  const [data, setData] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [filters, setFilters] = useState<any>({});
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [detail, setDetail] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [commentText, setCommentText] = useState('');
  const [form] = Form.useForm();

  const inlineUpdate = async (id: string, field: string, value: string) => {
    try {
      if (field === 'status') {
        await api.patch(`/bugs/${id}/status`, { status: value });
      } else {
        await api.patch(`/bugs/${id}`, { [field]: value || null });
      }
      load();
    } catch { message.error('更新失败'); }
  };

  const load = () => {
    const params = new URLSearchParams();
    if (projectId) params.set('project_id', projectId);
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v as string); });
    if (selectedNode) params.set('tab_node_id', selectedNode);
    api.get(`/bugs?${params}`).then((r) => setData(r.data));
    api.get('/bugs/stats' + (projectId ? `?project_id=${projectId}` : '')).then((r) => setStats(r.data));
  };

  useEffect(() => {
    api.get('/users').then((r) => setUsers(r.data));
    api.get('/projects').then((r) => setProjects(r.data));
  }, []);
  useEffect(() => { load(); }, [projectId, selectedNode, filters]);

  const onSubmit = async () => {
    const values = await form.validateFields();
    if (editing) {
      await api.patch(`/bugs/${editing.id}`, values);
      message.success('更新成功');
    } else {
      const body = { ...values, tab_node_id: selectedNode || undefined };
      if (projectId && !values.project_id) body.project_id = projectId;
      await api.post('/bugs', body);
      message.success('创建成功');
    }
    setOpen(false);
    setEditing(null);
    form.resetFields();
    load();
  };

  const openDetail = async (record: any) => {
    setDetail(record);
    const [c, a] = await Promise.all([
      api.get(`/bugs/${record.id}/comments`),
      api.get(`/bugs/${record.id}/attachments`),
    ]);
    setComments(c.data);
    setAttachments(a.data);
  };

  const onTransition = async (status: string) => {
    await api.patch(`/bugs/${detail.id}/status`, { status });
    message.success('状态已更新');
    const r = await api.get(`/bugs/${detail.id}`);
    setDetail(r.data);
    load();
  };

  const addComment = async () => {
    if (!commentText.trim()) return;
    await api.post(`/bugs/${detail.id}/comments`, { content: commentText });
    setCommentText('');
    const r = await api.get(`/bugs/${detail.id}/comments`);
    setComments(r.data);
  };

  const uploadAttachment = async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    await api.post(`/bugs/${detail.id}/attachments`, fd);
    message.success('上传成功');
    const r = await api.get(`/bugs/${detail.id}/attachments`);
    setAttachments(r.data);
    return false;
  };

  const getUserName = (id: string) => users.find((u: any) => u.id === id)?.username || '-';

  const pieOption = stats ? {
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: Object.entries(stats.by_severity).map(([k, v]) => ({ name: severityLabels[k] || k, value: v })) }],
  } : {};

  const barOption = stats ? {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: Object.keys(stats.by_status).map((k) => statusLabels[k] || k) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: Object.values(stats.by_status), color: '#1890ff' }],
  } : {};

  return (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <Space wrap>
          <Select allowClear placeholder="状态" style={{ width: 120 }} onChange={(v) => setFilters((f: any) => ({ ...f, status: v }))} options={Object.entries(statusLabels).map(([k, v]) => ({ label: v, value: k }))} />
          <Select allowClear placeholder="严重程度" style={{ width: 120 }} onChange={(v) => setFilters((f: any) => ({ ...f, severity: v }))} options={Object.entries(severityLabels).map(([k, v]) => ({ label: v, value: k }))} />
          <Select allowClear placeholder="指派人" style={{ width: 130 }} onChange={(v) => setFilters((f: any) => ({ ...f, assignee_id: v }))} options={users.map((u: any) => ({ label: u.username, value: u.id }))} />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setOpen(true); }}>新建缺陷</Button>
      </div>

      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}><Card title="严重程度分布" size="small"><ReactECharts option={pieOption} style={{ height: 250 }} /></Card></Col>
          <Col span={12}><Card title="状态分布" size="small"><ReactECharts option={barOption} style={{ height: 250 }} /></Card></Col>
        </Row>
      )}

      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '标题', dataIndex: 'title', render: (v: string, r: any) => (
            <EditableCell value={v} onSave={(val) => inlineUpdate(r.id, 'title', val)} />
          )},
          { title: '严重程度', dataIndex: 'severity', render: (v: string, r: any) => (
            <EditableCell value={v} type="select"
              options={Object.entries(severityLabels).map(([k, l]) => ({ label: l, value: k }))}
              onSave={(val) => inlineUpdate(r.id, 'severity', val)}
              render={<Tag color={severityColors[v]}>{severityLabels[v]}</Tag>} />
          )},
          { title: '状态', dataIndex: 'status', render: (v: string, r: any) => {
            const allowed = TRANSITIONS[v] || [];
            return (
              <EditableCell value={v} type="select"
                options={allowed.map((k) => ({ label: statusLabels[k], value: k }))}
                onSave={(val) => inlineUpdate(r.id, 'status', val)}
                render={<Tag color={statusColors[v]}>{statusLabels[v]}</Tag>} />
            );
          }},
          { title: '指派人', dataIndex: 'assignee_id', render: (v: string, r: any) => (
            <EditableCell value={v} type="select"
              options={users.map((u: any) => ({ label: u.username, value: u.id }))}
              onSave={(val) => inlineUpdate(r.id, 'assignee_id', val)}
              render={<span>{getUserName(v)}</span>} />
          )},
          { title: '创建时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
          {
            title: '操作', render: (_: any, record: any) => (
              <Space>
                <a onClick={() => openDetail(record)}>详情</a>
                <Popconfirm title="确认删除？" onConfirm={async () => { await api.delete(`/bugs/${record.id}`); message.success('已删除'); load(); }}>
                  <a style={{ color: 'red' }}>删除</a>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal title={editing ? '编辑缺陷' : '新建缺陷'} open={open} onOk={onSubmit} onCancel={() => { setOpen(false); setEditing(null); }} width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="severity" label="严重程度" initialValue="minor">
            <Select options={Object.entries(severityLabels).map(([k, v]) => ({ label: v, value: k }))} />
          </Form.Item>
          {!projectId && (
            <Form.Item name="project_id" label="所属项目" rules={[{ required: true }]}>
              <Select options={projects.map((p: any) => ({ label: p.name, value: p.id }))} />
            </Form.Item>
          )}
          <Form.Item name="assignee_id" label="指派人">
            <Select allowClear options={users.map((u: any) => ({ label: u.username, value: u.id }))} />
          </Form.Item>
          <Form.Item name="test_case_id" label="关联用例"><Input placeholder="用例ID（可选）" /></Form.Item>
        </Form>
      </Modal>

      <Modal title="缺陷详情" open={!!detail} onCancel={() => setDetail(null)} footer={null} width={700}>
        {detail && (
          <>
            <h3>{detail.title}</h3>
            <Space style={{ marginBottom: 16 }}>
              <Tag color={severityColors[detail.severity]}>{severityLabels[detail.severity]}</Tag>
              <Tag color={statusColors[detail.status]}>{statusLabels[detail.status]}</Tag>
            </Space>
            <p>{detail.description}</p>
            <div style={{ marginBottom: 16 }}>
              <strong>状态流转：</strong>
              <Space>
                {(TRANSITIONS[detail.status] || []).map((s: string) => (
                  <Button key={s} size="small" onClick={() => onTransition(s)}>{statusLabels[s]}</Button>
                ))}
              </Space>
            </div>

            <Card title="评论" size="small" style={{ marginBottom: 16 }}>
              <List
                dataSource={comments}
                renderItem={(c: any) => (
                  <List.Item actions={[<a onClick={async () => { await api.delete(`/bugs/${detail.id}/comments/${c.id}`); setComments(comments.filter((x: any) => x.id !== c.id)); }}>删除</a>]}>
                    <List.Item.Meta title={getUserName(c.author_id)} description={c.content} />
                    <span>{new Date(c.created_at).toLocaleString()}</span>
                  </List.Item>
                )}
              />
              <Space.Compact style={{ width: '100%', marginTop: 8 }}>
                <Input value={commentText} onChange={(e) => setCommentText(e.target.value)} placeholder="添加评论" onPressEnter={addComment} />
                <Button type="primary" onClick={addComment}>发送</Button>
              </Space.Compact>
            </Card>

            <Card title="附件" size="small">
              <List
                dataSource={attachments}
                renderItem={(a: any) => (
                  <List.Item actions={[
                    <a href={`/api/v1/bugs/attachments/${a.id}/download`} target="_blank" rel="noreferrer">下载</a>,
                    <a onClick={async () => { await api.delete(`/bugs/attachments/${a.id}`); setAttachments(attachments.filter((x: any) => x.id !== a.id)); }}>删除</a>,
                  ]}>
                    {a.filename} ({(a.filesize / 1024).toFixed(1)} KB)
                  </List.Item>
                )}
              />
              <Upload beforeUpload={(file) => { uploadAttachment(file); return false; }} showUploadList={false}>
                <Button icon={<UploadOutlined />} style={{ marginTop: 8 }}>上传附件</Button>
              </Upload>
            </Card>
          </>
        )}
      </Modal>
    </>
  );
};

export default BugsPage;

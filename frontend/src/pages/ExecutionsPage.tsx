import React, { useEffect, useState, useRef } from 'react';
import { Table, Tag, Button, Modal, Space } from 'antd';
import api from '@/services/api';

const statusColors: Record<string, string> = {
  pending: 'default', running: 'processing', passed: 'success', failed: 'error', error: 'warning', skipped: 'default',
};

const ExecutionsPage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [logOpen, setLogOpen] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const load = () => api.get('/executions').then((r) => setData(r.data));
  useEffect(() => { load(); }, []);

  // auto-scroll logs
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  const viewResults = async (id: string) => {
    const { data } = await api.get(`/executions/${id}/results`);
    setResults(data);
    setDetailOpen(true);
  };

  const viewLogs = (id: string) => {
    setLogs([]);
    setLogOpen(true);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/executions/${id}/logs`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setLogs((prev) => [...prev, data.msg]);
    };
    ws.onclose = () => {
      setLogs((prev) => [...prev, '--- Connection closed ---']);
    };
  };

  const closeLog = () => {
    wsRef.current?.close();
    wsRef.current = null;
    setLogOpen(false);
  };

  return (
    <>
      <h3>测试执行</h3>
      <Button onClick={load} style={{ marginBottom: 16 }}>刷新</Button>
      <Table
        rowKey="id"
        dataSource={data}
        columns={[
          { title: '名称', dataIndex: 'name' },
          { title: '状态', dataIndex: 'status', render: (v: string) => <Tag color={statusColors[v]}>{v.toUpperCase()}</Tag> },
          { title: '总数', dataIndex: 'total' },
          { title: '通过', dataIndex: 'passed', render: (v: number) => <span style={{ color: '#52c41a' }}>{v}</span> },
          { title: '失败', dataIndex: 'failed', render: (v: number) => <span style={{ color: '#ff4d4f' }}>{v}</span> },
          { title: '耗时(ms)', dataIndex: 'duration_ms' },
          { title: '创建时间', dataIndex: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
          {
            title: '操作',
            render: (_: any, r: any) => (
              <Space>
                <a onClick={() => viewResults(r.id)}>详情</a>
                {r.status === 'running' && <a onClick={() => viewLogs(r.id)} style={{ color: '#1890ff' }}>实时日志</a>}
              </Space>
            ),
          },
        ]}
      />

      <Modal title="执行详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={800}>
        <Table
          rowKey="id"
          dataSource={results}
          columns={[
            { title: '用例ID', dataIndex: 'case_id', ellipsis: true },
            { title: '状态', dataIndex: 'status', render: (v: string) => <Tag color={statusColors[v]}>{v.toUpperCase()}</Tag> },
            { title: '耗时(ms)', dataIndex: 'duration_ms' },
            { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
          ]}
        />
      </Modal>

      <Modal title="实时日志" open={logOpen} onCancel={closeLog} footer={null} width={800}>
        <div style={{
          background: '#1e1e1e', color: '#d4d4d4', padding: 16, borderRadius: 8,
          height: 400, overflowY: 'auto', fontFamily: 'Consolas, monospace', fontSize: 13, lineHeight: 1.6,
        }}>
          {logs.map((line, i) => (
            <div key={i} style={{
              color: line.startsWith('[DONE]') ? '#52c41a'
                : line.includes('FAILED') || line.includes('ERROR') ? '#ff4d4f'
                : line.startsWith('[START]') ? '#1890ff'
                : '#d4d4d4',
            }}>
              {line}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </Modal>
    </>
  );
};

export default ExecutionsPage;

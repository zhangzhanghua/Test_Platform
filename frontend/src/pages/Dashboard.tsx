import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import { ProjectOutlined, FileTextOutlined, PlayCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import api from '@/services/api';

const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState([]);
  const [executions, setExecutions] = useState<any[]>([]);

  useEffect(() => {
    api.get('/projects').then((r) => setProjects(r.data));
    api.get('/executions').then((r) => setExecutions(r.data));
  }, []);

  const passed = executions.filter((e) => e.status === 'passed').length;
  const failed = executions.filter((e) => e.status === 'failed').length;

  const trendOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: executions.slice(0, 10).map((_, i) => `#${i + 1}`).reverse() },
    yAxis: { type: 'value' },
    series: [
      { name: '通过', type: 'bar', stack: 'total', color: '#52c41a', data: executions.slice(0, 10).map((e: any) => e.passed).reverse() },
      { name: '失败', type: 'bar', stack: 'total', color: '#ff4d4f', data: executions.slice(0, 10).map((e: any) => e.failed).reverse() },
    ],
  };

  return (
    <>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="项目数" value={projects.length} prefix={<ProjectOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="执行总数" value={executions.length} prefix={<PlayCircleOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title="通过" value={passed} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="失败" value={failed} prefix={<FileTextOutlined />} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
      </Row>
      <Card title="最近执行趋势">
        <ReactECharts option={trendOption} style={{ height: 350 }} />
      </Card>
    </>
  );
};

export default Dashboard;

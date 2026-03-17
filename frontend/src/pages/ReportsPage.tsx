import React, { useEffect, useState } from 'react';
import { Card, Row, Col } from 'antd';
import ReactECharts from 'echarts-for-react';
import api from '@/services/api';

const ReportsPage: React.FC = () => {
  const [executions, setExecutions] = useState<any[]>([]);

  useEffect(() => { api.get('/executions').then((r) => setExecutions(r.data)); }, []);

  const total = executions.length;
  const passed = executions.filter((e) => e.status === 'passed').length;
  const failed = executions.filter((e) => e.status === 'failed').length;
  const other = total - passed - failed;

  const pieOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      data: [
        { value: passed, name: '通过', itemStyle: { color: '#52c41a' } },
        { value: failed, name: '失败', itemStyle: { color: '#ff4d4f' } },
        { value: other, name: '其他', itemStyle: { color: '#faad14' } },
      ],
    }],
  };

  const barOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: executions.slice(0, 20).map((e: any) => e.name).reverse() },
    yAxis: { type: 'value', name: '耗时(ms)' },
    series: [{ type: 'bar', data: executions.slice(0, 20).map((e: any) => e.duration_ms).reverse(), color: '#1890ff' }],
  };

  return (
    <>
      <h3>测试报告</h3>
      <Row gutter={16}>
        <Col span={12}>
          <Card title="执行结果分布"><ReactECharts option={pieOption} style={{ height: 350 }} /></Card>
        </Col>
        <Col span={12}>
          <Card title="执行耗时趋势"><ReactECharts option={barOption} style={{ height: 350 }} /></Card>
        </Col>
      </Row>
    </>
  );
};

export default ReportsPage;

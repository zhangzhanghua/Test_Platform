import React, { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { Layout, Menu, Tag, Space, Tree } from 'antd';
import {
  DashboardOutlined, ProjectOutlined, FileTextOutlined, PlayCircleOutlined,
  BarChartOutlined, CloudServerOutlined, BellOutlined, ApiOutlined,
  TeamOutlined, SettingOutlined, BugOutlined, FolderOutlined, AppstoreOutlined,
} from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';
import api from '@/services/api';

const { Header, Sider, Content } = Layout;

const iconMap: Record<string, React.ReactNode> = {
  DashboardOutlined: <DashboardOutlined />, ProjectOutlined: <ProjectOutlined />,
  FileTextOutlined: <FileTextOutlined />, PlayCircleOutlined: <PlayCircleOutlined />,
  BarChartOutlined: <BarChartOutlined />, CloudServerOutlined: <CloudServerOutlined />,
  BellOutlined: <BellOutlined />, ApiOutlined: <ApiOutlined />,
  TeamOutlined: <TeamOutlined />, SettingOutlined: <SettingOutlined />,
  BugOutlined: <BugOutlined />,
};

const TREE_PATHS = ['/testcases', '/bugs'];

interface SiderTreeProps {
  label: string;
  icon: React.ReactNode;
  path: string;
  scope: 'testcase' | 'bug';
  projects: any[];
  navigate: (path: string) => void;
  currentPath: string;
  currentProjectId?: string;
  currentNodeId?: string | null;
}

const SiderTree: React.FC<SiderTreeProps> = ({ label, icon, path, scope, projects, navigate, currentPath, currentProjectId, currentNodeId }) => {
  const [treeMap, setTreeMap] = useState<Record<string, any[]>>({});
  const [collapsed, setCollapsed] = useState(currentPath !== path);

  useEffect(() => {
    if (projects.length === 0) return;
    Promise.all(projects.map((p) =>
      api.get('/tab-nodes', { params: { project_id: p.id, scope } }).then((r) => ({ id: p.id, nodes: r.data }))
    )).then((results) => {
      const map: Record<string, any[]> = {};
      results.forEach((r) => { map[r.id] = r.nodes; });
      setTreeMap(map);
    });
  }, [projects, scope]);

  const buildNodes = (nodes: any[]): DataNode[] =>
    nodes.map((n: any) => ({
      key: n.id,
      title: n.name,
      icon: <FolderOutlined />,
      children: n.children?.length ? buildNodes(n.children) : [],
    }));

  const treeData: DataNode[] = projects.map((p) => ({
    key: `proj_${p.id}`,
    title: p.name,
    icon: <AppstoreOutlined />,
    children: buildNodes(treeMap[p.id] || []),
  }));

  const nav = (projectId: string, nodeId?: string | null) => {
    const params = new URLSearchParams();
    params.set('project_id', projectId);
    if (nodeId) params.set('tab_node_id', nodeId);
    navigate(`${path}?${params}`);
  };

  const selectedKey = currentPath === path
    ? (currentNodeId || (currentProjectId ? `proj_${currentProjectId}` : undefined))
    : undefined;

  return (
    <div className="sider-tree-section">
      <div
        style={{ padding: '8px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, color: currentPath === path ? '#1890ff' : '#ffffffa6' }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <span style={{ transition: 'transform 0.2s', transform: collapsed ? 'rotate(-90deg)' : 'rotate(0)', fontSize: 10 }}>▼</span>
        {icon} <span>{label}</span>
      </div>
      {!collapsed && (
        <div style={{ padding: '0 8px 8px' }}>
          <Tree
            showIcon
            treeData={treeData}
            selectedKeys={selectedKey ? [selectedKey] : []}
            defaultExpandAll={false}
            onSelect={(keys) => {
              if (!keys.length) return;
              const key = String(keys[0]);
              if (key.startsWith('proj_')) {
                nav(key.replace('proj_', ''), null);
              } else {
                // find which project this node belongs to
                for (const p of projects) {
                  const findInNodes = (nodes: any[]): boolean => {
                    for (const n of nodes) {
                      if (n.id === key) return true;
                      if (n.children?.length && findInNodes(n.children)) return true;
                    }
                    return false;
                  };
                  if (findInNodes(treeMap[p.id] || [])) {
                    nav(p.id, key);
                    break;
                  }
                }
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [user, setUser] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);

  const currentProjectId = searchParams.get('project_id') || undefined;
  const currentNodeId = searchParams.get('tab_node_id') || undefined;

  useEffect(() => {
    api.get('/auth/me').then((r) => setUser(r.data)).catch(() => {
      localStorage.removeItem('token');
      navigate('/login');
    });
    api.get('/projects').then((r) => setProjects(r.data));
  }, []);

  const buildMenuItems = (menus: any[]): any[] =>
    menus.filter((m) => !TREE_PATHS.includes(m.path)).map((m) => ({
      key: m.path || m.id,
      icon: iconMap[m.icon] || null,
      label: m.name,
      children: m.children?.length ? buildMenuItems(m.children) : undefined,
    }));

  const menuItems = user?.menus ? buildMenuItems(user.menus) : [];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={220} style={{ overflow: 'auto' }}>
        <div style={{ height: 48, margin: 16, color: '#fff', fontSize: 18, fontWeight: 700, textAlign: 'center', lineHeight: '48px' }}>
          测试平台
        </div>
        <Menu
          theme="dark" mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
        <SiderTree label="用例管理" icon={<FileTextOutlined />} path="/testcases" scope="testcase"
          projects={projects} navigate={navigate} currentPath={location.pathname}
          currentProjectId={currentProjectId} currentNodeId={currentNodeId} />
        <SiderTree label="缺陷管理" icon={<BugOutlined />} path="/bugs" scope="bug"
          projects={projects} navigate={navigate} currentPath={location.pathname}
          currentProjectId={currentProjectId} currentNodeId={currentNodeId} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <Space>
            {user && (
              <>
                <span>{user.username}</span>
                {user.roles?.map((r: any) => <Tag key={r.id} color="blue">{r.name}</Tag>)}
              </>
            )}
            <a onClick={() => { localStorage.removeItem('token'); navigate('/login'); }}>退出登录</a>
          </Space>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8, minHeight: 360 }}>
          <Outlet />
        </Content>
      </Layout>
      <style>{`
        .sider-tree-section .ant-tree { color: #ffffffa6; background: transparent; }
        .sider-tree-section .ant-tree .ant-tree-node-content-wrapper { color: #ffffffa6; }
        .sider-tree-section .ant-tree .ant-tree-node-content-wrapper:hover { background: rgba(255,255,255,0.08); }
        .sider-tree-section .ant-tree .ant-tree-node-selected .ant-tree-node-content-wrapper,
        .sider-tree-section .ant-tree .ant-tree-node-content-wrapper.ant-tree-node-selected { background: #1890ff !important; color: #fff !important; }
        .sider-tree-section .ant-tree-switcher { color: #ffffffa6; }
        .sider-tree-section .ant-tree .ant-tree-treenode-selected .ant-tree-node-content-wrapper { background: #1890ff !important; color: #fff !important; }
      `}</style>
    </Layout>
  );
};

export default MainLayout;

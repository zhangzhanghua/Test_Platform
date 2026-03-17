import React, { useEffect, useState } from 'react';
import { Tree, Button, Input, Dropdown, Modal, message } from 'antd';
import { PlusOutlined, FolderOutlined } from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';
import api from '@/services/api';

export interface CategoryTreeProps {
  projectId: string;
  scope: 'testcase' | 'bug';
  onSelect: (nodeId: string | null) => void;
  selectedNodeId?: string | null;
}

interface TreeNode {
  id: string;
  name: string;
  sort_order: number;
  parent_id: string | null;
  children: TreeNode[];
}

const toAntTree = (nodes: TreeNode[]): DataNode[] =>
  nodes.map((n) => ({
    key: n.id,
    title: n.name,
    icon: <FolderOutlined />,
    children: n.children?.length ? toAntTree(n.children) : [],
  }));

const CategoryTree: React.FC<CategoryTreeProps> = ({ projectId, scope, onSelect, selectedNodeId }) => {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [nameModal, setNameModal] = useState<{ visible: boolean; parentId: string | null; editId: string | null }>({ visible: false, parentId: null, editId: null });
  const [name, setName] = useState('');

  const load = () => {
    api.get('/tab-nodes', { params: { project_id: projectId, scope } }).then((r) => setTree(r.data));
  };

  useEffect(() => {
    if (projectId) load();
    else setTree([]);
  }, [projectId, scope]);

  const handleSelect = (keys: React.Key[]) => {
    const id = keys.length ? String(keys[0]) : null;
    onSelect(id);
  };

  const openCreate = (parentId: string | null, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setName('');
    setNameModal({ visible: true, parentId, editId: null });
  };

  const openRename = (id: string, currentName: string) => {
    setName(currentName);
    setNameModal({ visible: true, parentId: null, editId: id });
  };

  const handleOk = async () => {
    if (!name.trim()) return;
    if (nameModal.editId) {
      await api.patch(`/tab-nodes/${nameModal.editId}`, { name });
    } else {
      await api.post('/tab-nodes', { name, scope, project_id: projectId, parent_id: nameModal.parentId });
    }
    setNameModal({ visible: false, parentId: null, editId: null });
    load();
  };

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除此分类及其子分类？',
      onOk: async () => {
        await api.delete(`/tab-nodes/${id}`);
        message.success('已删除');
        if (selectedNodeId === id) onSelect(null);
        load();
      },
    });
  };

  const findNode = (nodes: TreeNode[], id: string): TreeNode | undefined => {
    for (const n of nodes) {
      if (n.id === id) return n;
      const found = findNode(n.children || [], id);
      if (found) return found;
    }
  };

  const treeData = toAntTree(tree);

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 8, display: 'flex', gap: 4 }}>
        <Button size="small" type={!selectedNodeId ? 'primary' : 'default'} onClick={() => onSelect(null)}>全部</Button>
        <Button size="small" icon={<PlusOutlined />} onClick={(e) => openCreate(null, e)}>新增</Button>
      </div>
      <div style={{ overflow: 'auto' }}>
        <Tree
          showIcon
          treeData={treeData}
          selectedKeys={selectedNodeId ? [selectedNodeId] : []}
          onSelect={handleSelect}
          titleRender={(node) => (
            <Dropdown
              trigger={['contextMenu']}
              menu={{
                items: [
                  { key: 'add', label: '新增子节点', onClick: () => openCreate(String(node.key)) },
                  { key: 'rename', label: '重命名', onClick: () => { const n = findNode(tree, String(node.key)); if (n) openRename(n.id, n.name); } },
                  { key: 'delete', label: '删除', danger: true, onClick: () => handleDelete(String(node.key)) },
                ],
              }}
            >
              <span>{String(node.title)}</span>
            </Dropdown>
          )}
        />
      </div>
      <Modal
        title={nameModal.editId ? '重命名' : '新增分类'}
        open={nameModal.visible}
        onOk={handleOk}
        onCancel={() => setNameModal({ visible: false, parentId: null, editId: null })}
      >
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="分类名称" onPressEnter={handleOk} />
      </Modal>
    </div>
  );
};

export default CategoryTree;

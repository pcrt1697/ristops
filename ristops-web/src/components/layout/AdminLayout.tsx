import { useState } from 'react';
import { Layout, Menu } from 'antd';
import { EnvironmentOutlined, UserOutlined } from '@ant-design/icons';
import { Outlet, useNavigate } from 'react-router-dom';

const { Sider, Content } = Layout;

export default function AdminLayout() {
  const [collapsed, setCollapsed] = useState(true);
  const navigate = useNavigate();

  const menuItems = [
    {
      key: 'venues',
      icon: <EnvironmentOutlined />,
      label: 'Venues',
      onClick: () => void navigate('/admin/venues'),
    },
    {
      key: 'users',
      icon: <UserOutlined />,
      label: 'Users',
      onClick: () => void navigate('/admin/users'),
    },
  ];

  return (
    <Layout style={{ minHeight: '100%' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        collapsedWidth={56}
      >
        <Menu mode="inline" items={menuItems} style={{ height: '100%' }} />
      </Sider>
      <Content>
        <Outlet />
      </Content>
    </Layout>
  );
}

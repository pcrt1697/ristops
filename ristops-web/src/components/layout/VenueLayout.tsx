import { useState } from 'react';
import { Layout, Menu } from 'antd';
import { OrderedListOutlined, CalendarOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useParams } from 'react-router-dom';

const { Sider, Content } = Layout;

export default function VenueLayout() {
  const [collapsed, setCollapsed] = useState(true);
  const navigate = useNavigate();
  const { venueId } = useParams<{ venueId: string }>();

  const menuItems = [
    {
      key: 'orders',
      icon: <OrderedListOutlined />,
      label: 'Orders',
      onClick: () => void navigate(`/venues/${venueId}/orders`),
    },
    {
      key: 'reservations',
      icon: <CalendarOutlined />,
      label: 'Reservations',
      onClick: () => void navigate(`/venues/${venueId}/reservations`),
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

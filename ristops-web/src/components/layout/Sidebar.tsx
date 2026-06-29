import { useState } from 'react';
import { Button, Layout, Menu, type MenuProps, theme, Typography } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SafetyCertificateOutlined,
  ShopOutlined,
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import logo from '../../assets/ristops-logo-icon.png';

const { Sider } = Layout;
const { Text } = Typography;

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  const { isAllowed: canManageApp } = useCan(
    { type: ResourceType.App, id: '*' },
    'app:*',
  );

  const items: MenuProps['items'] = [];
  if (location.pathname.startsWith('/admin') && canManageApp) {
    items.push(
      {
        key: '/admin/venues',
        icon: <ShopOutlined />,
        label: 'Venues',
        onClick: () => void navigate('/admin/venues'),
      },
      {
        key: '/admin/access-control',
        icon: <SafetyCertificateOutlined />,
        label: 'Access Control',
        onClick: () => void navigate('/admin/access-control'),
      },
    );
  }

  // Highlight the item whose path is a prefix of the current location.
  const selectedKey = items
    .map((item) => item?.key)
    .filter((key): key is string => typeof key === 'string')
    .find((key) => location.pathname.startsWith(key));

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      collapsedWidth={60}
      trigger={null}
      theme="light"
      style={{
        height: 'calc(100vh - 32px)',
        position: 'sticky',
        insetInlineStart: 0,
        top: 16,
        overflow: 'hidden',
        borderRadius: token.borderRadiusLG,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div
          role="button"
          onClick={() => void navigate('/')}
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            paddingLeft: collapsed ? 0 : 20,
            gap: 10,
            cursor: 'pointer',
            borderBottom: `1px solid ${token.colorSplit}`,
          }}
        >
          <img src={logo} alt="RistOps" style={{ height: 24, width: 24 }} />
          {!collapsed && (
            <Text strong style={{ fontSize: 16 }}>
              RistOps
            </Text>
          )}
        </div>

        <Menu
          mode="inline"
          selectedKeys={selectedKey ? [selectedKey] : []}
          items={items}
          style={{ flex: 1, overflow: 'auto', borderInlineEnd: 0 }}
        />

        <Button
          type="text"
          block
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setCollapsed(!collapsed)}
          style={{
            height: 48,
            borderTop: `1px solid ${token.colorSplit}`,
            borderRadius: 0,
          }}
        />
      </div>
    </Sider>
  );
}

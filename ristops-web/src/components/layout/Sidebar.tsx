import { useState } from 'react';
import { Button, Layout, Menu, theme, Typography } from 'antd';
import {
  HomeOutlined,
  VerticalLeftOutlined,
  VerticalRightOutlined,
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import logo from '../../assets/ristops-logo-icon.png';

const { Sider } = Layout;
const { Text } = Typography;

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  const topItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Home',
      onClick: () => void navigate('/'),
    },
  ];

  return (
    <div style={{ position: 'relative' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        collapsedWidth={60}
        trigger={null}
        theme="light"
        style={{
          overflow: 'auto',
          height: 'calc(100vh - 32px)',
          position: 'sticky',
          insetInlineStart: 0,
          top: 16,
          scrollbarWidth: 'thin',
          scrollbarGutter: 'stable',
          borderRadius: token.borderRadiusLG,
        }}
      >
        <div
          style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
        >
          <div
            style={{
              height: 64,
              display: 'flex',
              alignItems: 'center',
              justifyContent: collapsed ? 'center' : 'flex-start',
              paddingLeft: collapsed ? 0 : 20,
              gap: 10,
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
            selectedKeys={[location.pathname]}
            items={topItems}
            style={{ borderInlineEnd: 0, flex: 1 }}
          />
        </div>
      </Sider>

      <Button
        shape="circle"
        size="small"
        icon={collapsed ? <VerticalRightOutlined /> : <VerticalLeftOutlined />}
        onClick={() => setCollapsed(!collapsed)}
        style={{
          position: 'absolute',
          right: -12,
          top: 20,
          zIndex: 1,
          boxShadow: token.boxShadowSecondary,
          background: token.colorBgContainer,
          borderColor: token.colorBorderSecondary,
        }}
      />
    </div>
  );
}

import {
  Button,
  Dropdown,
  Flex,
  Layout,
  type MenuProps,
  Modal,
  theme,
} from 'antd';
import {
  LogoutOutlined,
  MenuOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useCan, useLogout } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import logo from '../../assets/ristops-logo-icon.png';
import VenueControl from './VenueControl.tsx';

const { Header } = Layout;

export default function TopBar() {
  const { token } = theme.useToken();
  const navigate = useNavigate();
  const { mutate: logout } = useLogout();

  const { isAllowed: canManageApp } = useCan(
    { type: ResourceType.App, id: '*' },
    'app:*',
  );

  const items: MenuProps['items'] = [];
  if (canManageApp) {
    items.push(
      {
        key: '/admin',
        icon: <SafetyCertificateOutlined />,
        label: 'Administration',
        onClick: () => void navigate('/admin/access-control'),
      },
      { type: 'divider' },
    );
  }
  items.push({
    key: 'account',
    label: 'Account',
    type: 'group',
    children: [
      {
        key: '/profile',
        icon: <UserOutlined />,
        label: 'Profile',
        onClick: () => void navigate('/profile'),
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Logout',
        danger: true,
        onClick: () => {
          Modal.confirm({
            title: 'Log out',
            content: 'Are you sure you want to log out?',
            okText: 'Log out',
            okType: 'danger',
            cancelText: 'Cancel',
            onOk: () => logout(),
          });
        },
      },
    ],
  });

  return (
    <Header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        background: token.colorBgContainer,
        borderRadius: token.borderRadiusLG,
      }}
    >
      <Flex align="center" gap={12}>
        <img src={logo} alt="RistOps" style={{ height: 24, width: 24 }} />
        <span
          style={{ width: 1, height: 24, background: token.colorSplit }}
          aria-hidden
        />
        <VenueControl />
      </Flex>
      <Dropdown menu={{ items }} trigger={['click']} placement="bottomRight">
        <Button icon={<MenuOutlined />} />
      </Dropdown>
    </Header>
  );
}

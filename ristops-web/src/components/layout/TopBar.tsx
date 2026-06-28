import {
  Button,
  Dropdown,
  Layout,
  type MenuProps,
  Modal,
  Spin,
  theme,
} from 'antd';
import {
  LogoutOutlined,
  MenuOutlined,
  SafetyCertificateOutlined,
  ShopOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useCan, useLogout } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';

const { Header } = Layout;

export default function TopBar() {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const navigate = useNavigate();
  const { mutate: logout } = useLogout();

  const { isAllowed: canManageApp, isLoading: isLoading } = useCan(
    {
      type: ResourceType.App,
      id: '*',
    },
    'app:*',
  );
  if (isLoading) return <Spin fullscreen />;

  const adminItems: MenuProps['items'] = [];
  if (canManageApp) {
    adminItems.push({
      key: '/admin/venues',
      icon: <ShopOutlined />,
      label: 'Venues',
      onClick: () => void navigate('/admin/venues'),
    });
    adminItems.push({
      key: '/admin/access-control',
      icon: <SafetyCertificateOutlined />,
      label: 'Access Control',
      onClick: () => void navigate('/admin/access-control'),
    });
  }

  const items: MenuProps['items'] = [];
  if (adminItems.length > 0) {
    items.push(
      {
        key: 'administration',
        label: 'Administration',
        type: 'group',
        children: adminItems,
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
        padding: '0 24px',
        background: colorBgContainer,
        borderRadius: borderRadiusLG,
      }}
    >
      <div>Current page name</div>
      <Dropdown menu={{ items }} trigger={['click']} placement="bottomRight">
        <Button icon={<MenuOutlined />} />
      </Dropdown>
    </Header>
  );
}

import { Button, Dropdown, Layout } from 'antd';
import {
  HomeOutlined,
  LogoutOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth, useLogout } from '../../domain/auth/auth.hooks.ts';

const { Header } = Layout;

export default function TopBar() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { mutate: logout } = useLogout();

  const isAdmin = false; // todo: derive from user roles

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => void navigate('/profile'),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      // todo: test this
      onClick: () => logout(),
    },
  ];

  return (
    <Header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
      }}
    >
      <Link to="/">
        <HomeOutlined style={{ fontSize: 20, color: 'white' }} />
      </Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {isAdmin && (
          <Button
            type="text"
            icon={<SettingOutlined style={{ color: 'white' }} />}
            onClick={() => void navigate('/admin')}
          />
        )}
        <Dropdown
          menu={{ items: userMenuItems }}
          trigger={['click']}
          placement="bottomRight"
        >
          <Button
            type="text"
            icon={<UserOutlined style={{ color: 'white' }} />}
          />
        </Dropdown>
      </div>
    </Header>
  );
}

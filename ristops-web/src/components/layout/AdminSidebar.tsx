import { type MenuProps } from 'antd';
import {
  AppstoreOutlined,
  KeyOutlined,
  SafetyCertificateOutlined,
  ShopOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import Sidebar from './Sidebar.tsx';

export default function AdminSidebar() {
  const navigate = useNavigate();
  const { isAllowed: canManageApp } = useCan(
    { type: ResourceType.App, id: '*' },
    'app:*',
  );

  const go = (path: string) => () => void navigate(path);

  const items: MenuProps['items'] = canManageApp
    ? [
        {
          key: 'manage',
          type: 'group',
          label: 'Manage',
          children: [
            {
              key: '/admin/venues',
              icon: <ShopOutlined />,
              label: 'Venues',
              onClick: go('/admin/venues'),
            },
          ],
        },
        {
          key: 'access-control',
          type: 'group',
          label: 'Access Control',
          children: [
            {
              key: '/admin/access-control/app',
              icon: <AppstoreOutlined />,
              label: 'App',
              onClick: go('/admin/access-control/app'),
            },
            {
              key: '/admin/access-control/roles',
              icon: <SafetyCertificateOutlined />,
              label: 'Roles',
              onClick: go('/admin/access-control/roles'),
            },
            {
              key: '/admin/access-control/permissions',
              icon: <KeyOutlined />,
              label: 'Permissions',
              onClick: go('/admin/access-control/permissions'),
            },
          ],
        },
      ]
    : [];

  return <Sidebar items={items} />;
}

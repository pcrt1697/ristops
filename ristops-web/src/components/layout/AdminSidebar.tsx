import { type MenuProps } from 'antd';
import { SafetyCertificateOutlined, ShopOutlined } from '@ant-design/icons';
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

  const items: MenuProps['items'] = canManageApp
    ? [
        {
          key: '/admin/access-control',
          icon: <SafetyCertificateOutlined />,
          label: 'Access Control',
          onClick: () => void navigate('/admin/access-control'),
        },
        {
          key: '/admin/venues',
          icon: <ShopOutlined />,
          label: 'Venues',
          onClick: () => void navigate('/admin/venues'),
        },
      ]
    : [];

  return <Sidebar items={items} />;
}

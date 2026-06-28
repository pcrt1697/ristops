import { Tabs, type TabsProps } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

const BASE_PATH = '/admin/access-control';

const items: TabsProps['items'] = [
  { key: 'app', label: 'App' },
  { key: 'roles', label: 'Roles' },
  { key: 'permissions', label: 'Permissions' },
];

export default function AdminAclPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const activeKey = location.pathname.split('/').pop() ?? 'roles';

  return (
    <div>
      <Tabs
        activeKey={activeKey}
        items={items}
        onChange={(key) => void navigate(`${BASE_PATH}/${key}`)}
      />
      <Outlet />
    </div>
  );
}

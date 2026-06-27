import { Tabs, type TabsProps } from 'antd';
import RolesTab from '../../components/acl/RolesTab.tsx';

export default function AdminAclPage() {
  const items: TabsProps['items'] = [
    {
      key: 'roles',
      label: 'Roles',
      children: <RolesTab />,
    },
    {
      key: 'permissions',
      label: 'Permissions',
      children: 'List of permissions',
    },
  ];
  return (
    <div>
      <Tabs defaultActiveKey="roles" items={items} />
    </div>
  );
}

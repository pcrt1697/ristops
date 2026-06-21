import { Tabs, type TabsProps } from 'antd';

export default function AdminAclPage() {
  // todo: define permissions to enable tabs
  const items: TabsProps['items'] = [
    {
      key: 'roles',
      label: 'Roles',
      children: 'List of roles',
    },
    {
      key: 'permissions',
      label: 'Permissions',
      children: 'List of permissions',
    },
  ];
  return (
    <div>
      <Tabs defaultActiveKey="roles" items={items} />;
    </div>
  );
}

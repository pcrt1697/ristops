import { useState } from 'react';
import { Card, Drawer, Flex, Input, Result, Spin, Tag, Typography } from 'antd';
import { useCan, useListRoles } from '../../domain/auth/auth.hooks.ts';
import {
  formatPermissionId,
  PERMISSION_DESCRIPTIONS,
} from '../../domain/auth/permissions.ts';
import type { Role } from '../../services/graphql/graphql.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';

const { Meta } = Card;
const { Search } = Input;
const { Text } = Typography;

function PermissionRow({ id }: { id: string }) {
  return (
    <Flex vertical gap={2} style={{ paddingBlock: 6 }}>
      <Tag style={{ width: 'fit-content' }}>{formatPermissionId(id)}</Tag>
      <Text type="secondary" style={{ fontSize: 12 }}>
        {PERMISSION_DESCRIPTIONS[id] ?? id}
      </Text>
    </Flex>
  );
}

function RoleDrawer({
  role,
  onClose,
}: {
  role: Role | null;
  onClose: () => void;
}) {
  return (
    <Drawer
      title={role?.name}
      open={role !== null}
      onClose={onClose}
      width={360}
    >
      {role && (
        <Flex vertical gap={4}>
          <Text type="secondary" style={{ marginBottom: 16 }}>
            {role.description}
          </Text>
          {role.permissions.map((p) => (
            <PermissionRow key={p} id={p} />
          ))}
        </Flex>
      )}
    </Drawer>
  );
}

export default function RolesTab() {
  const [search, setSearch] = useState('');
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const { isAllowed, isLoading: isLoadingCan } = useCan(
    { type: ResourceType.App, id: '*' },
    'role~list',
  );
  const { data, isLoading } = useListRoles({}, isAllowed);

  if (isLoading || isLoadingCan) return <Spin />;
  if (!isAllowed)
    return <Result status="403" title="You don't have permission to view roles" />;

  const roles = (data?.listRoles.roles ?? []).filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <Search
        placeholder="Search roles"
        allowClear
        onChange={(e) => setSearch(e.target.value)}
        style={{ maxWidth: 320, marginBottom: 24 }}
      />
      <Flex wrap gap={16}>
        {roles.map((role) => (
          <Card
            key={role.id}
            hoverable
            style={{ width: 280 }}
            onClick={() => setSelectedRole(role)}
          >
            <Meta title={role.name} description={role.description} />
          </Card>
        ))}
      </Flex>
      <RoleDrawer role={selectedRole} onClose={() => setSelectedRole(null)} />
    </>
  );
}

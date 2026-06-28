import { useState } from 'react';
import {
  AutoComplete,
  Card,
  Drawer,
  Flex,
  Result,
  Select,
  Spin,
  Typography,
} from 'antd';
import { useCan, useListRoles } from '../../domain/auth/auth.hooks.ts';
import {
  formatPermissionId,
  PERMISSION_DESCRIPTIONS,
} from '../../domain/auth/permissions.ts';
import type { ListRolesInput, Role } from '../../services/graphql/graphql.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useDebounced, useSearchParamState } from '../../commons/hooks.ts';
import { matchOption, orNull } from '../../commons/utils.ts';

const { Meta } = Card;
const { Text, Title } = Typography;

function PermissionRow({ id }: { id: string }) {
  return (
    <Card size="small">
      <Meta
        title={id}
        description={PERMISSION_DESCRIPTIONS[id] ?? formatPermissionId(id)}
      />
    </Card>
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
      size={360}
    >
      {role && (
        <Flex vertical gap={4}>
          <Text type="secondary" style={{ marginBottom: 16 }}>
            {role.description}
          </Text>
          <Title level={4}>Permissions</Title>
          {role.permissions.sort().map((p) => (
            <PermissionRow key={p} id={p} />
          ))}
        </Flex>
      )}
    </Drawer>
  );
}

export default function RolesTab() {
  const [roleName, setRoleName] = useSearchParamState('roleName');
  const [permission, setPermission] = useSearchParamState('permission');
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const debouncedRoleName = useDebounced(roleName);
  const debouncedPermission = useDebounced(permission);

  const { isAllowed, isLoading: isLoadingCan } = useCan(
    { type: ResourceType.App, id: '*' },
    'role:list',
  );

  const query: ListRolesInput = {
    roleName: orNull(debouncedRoleName),
    permission: orNull(debouncedPermission),
  };
  const { data, isLoading } = useListRoles(query, isAllowed);

  const roles =
    data?.listRoles.roles.sort((a, b) => a.name.localeCompare(b.name)) ?? [];
  const roleNameOptions = roles.map((r) => ({ value: r.name }));
  const permissionOptions = [...new Set(roles.flatMap((r) => r.permissions))]
    .map((p) => ({ value: p }))
    .sort();

  if (isLoadingCan) return <Spin />;
  if (!isAllowed)
    return (
      <Result status="403" title="You don't have permission to view roles" />
    );

  return (
    <>
      <Flex gap={12} style={{ marginBottom: 24 }}>
        <AutoComplete
          placeholder="Role name"
          allowClear
          value={roleName}
          options={roleNameOptions}
          onChange={setRoleName}
          showSearch={{ filterOption: matchOption }}
          style={{ width: 200 }}
        />
        <Select
          placeholder="Permission"
          allowClear
          value={permission || undefined}
          options={permissionOptions}
          onChange={(v) => setPermission(v ?? '')}
          showSearch={{ filterOption: matchOption }}
          style={{ width: 200 }}
        />
      </Flex>
      {isLoading ? (
        <Spin />
      ) : (
        <Flex wrap gap={16}>
          {roles.map((role) => (
            <Card
              size="default"
              key={role.id}
              hoverable
              style={{ width: 280 }}
              onClick={() => setSelectedRole(role)}
            >
              <Meta title={role.name} description={role.description} />
            </Card>
          ))}
        </Flex>
      )}
      <RoleDrawer role={selectedRole} onClose={() => setSelectedRole(null)} />
    </>
  );
}

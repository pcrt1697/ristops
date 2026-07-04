import { useState } from 'react';
import { AutoComplete, Card, Flex, Result, Select, Spin } from 'antd';
import { useCan, useListRoles } from '../../domain/auth/auth.hooks.ts';
import type { ListRolesInput, Role } from '../../services/graphql/graphql.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useDebounced, useSearchParamState } from '../../commons/hooks.ts';
import { matchOption, orNull } from '../../commons/utils.ts';
import { formatScope, ROLE_SCOPES } from '../../domain/auth/authz.utils.ts';
import RoleDetailDrawer from './RoleDetailDrawer.tsx';
import RoleScopeTag from './RoleScopeTag.tsx';

const { Meta } = Card;

export default function RolesTab() {
  const [roleName, setRoleName] = useSearchParamState('roleName');
  const [permission, setPermission] = useSearchParamState('permission');
  const [scope, setScope] = useSearchParamState('scope');
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
    scope: scope ? (scope as ResourceType) : null,
  };
  const { data, isLoading } = useListRoles(query, isAllowed);

  const roles =
    data?.listRoles.roles.sort((a, b) => a.name.localeCompare(b.name)) ?? [];
  const roleNameOptions = roles.map((r) => ({ value: r.name }));
  const permissionOptions = [...new Set(roles.flatMap((r) => r.permissions))]
    .map((p) => ({ value: p }))
    .sort();
  const scopeOptions = ROLE_SCOPES.map((s) => ({
    label: formatScope(s),
    value: s,
  }));

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
          placeholder="Scope"
          allowClear
          value={scope || undefined}
          options={scopeOptions}
          onChange={(v) => setScope(v ?? '')}
          style={{ width: 160 }}
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
              <Meta
                title={
                  <Flex align="center" justify="space-between" gap={8}>
                    <span>{role.name}</span>
                    <RoleScopeTag scope={role.scope} />
                  </Flex>
                }
                description={role.description}
              />
            </Card>
          ))}
        </Flex>
      )}
      <RoleDetailDrawer
        role={selectedRole}
        onClose={() => setSelectedRole(null)}
      />
    </>
  );
}

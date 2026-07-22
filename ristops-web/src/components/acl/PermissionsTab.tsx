import { AutoComplete, Button, Card, Flex, Result, Spin } from 'antd';
import { TeamOutlined } from '@ant-design/icons';
import { createSearchParams, useNavigate } from 'react-router-dom';
import { useCan, useListPermissions } from '../../domain/auth/auth.hooks.ts';
import {
  formatPermissionId,
  PERMISSION_DESCRIPTIONS,
} from '../../domain/auth/permissions.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useDebounced, useSearchParamState } from '../../commons/hooks.ts';
import { matchOption, orNull } from '../../commons/utils.ts';

const { Meta } = Card;

export default function PermissionsTab() {
  const navigate = useNavigate();
  const [query, setQuery] = useSearchParamState('permission');
  const debouncedFilter = useDebounced(query);

  const viewRolesWithPermission = (permission: string) =>
    void navigate({
      pathname: '/admin/access-control/roles',
      search: createSearchParams({ permission }).toString(),
    });

  const { isAllowed, isLoading: isLoadingCan } = useCan(
    { type: ResourceType.App, id: '*' },
    'permission:list',
  );

  const { data, isLoading } = useListPermissions(
    orNull(debouncedFilter),
    isAllowed,
  );

  const permissions = data?.listPermissions.permissions.sort() ?? [];
  const permissionOptions = permissions.map((p) => ({ value: p })).sort();

  if (isLoadingCan) return <Spin />;
  if (!isAllowed)
    return (
      <Result status="403" title="You don't have permission to view roles" />
    );

  return (
    <>
      <Flex gap={12} style={{ marginBottom: 24 }}>
        <AutoComplete
          placeholder="Permission"
          allowClear
          value={query}
          options={permissionOptions}
          onChange={setQuery}
          showSearch={{ filterOption: matchOption }}
          style={{ width: 200 }}
        />
      </Flex>
      {isLoading ? (
        <Spin />
      ) : (
        <Flex wrap gap={16}>
          {permissions.map((permission) => (
            <Card
              key={permission}
              size="default"
              style={{ width: '45%', display: 'flex', flexDirection: 'column' }}
              styles={{ body: { flex: 1 }, actions: { flexShrink: 0 } }}
              actions={[
                <Button
                  key="roles"
                  type="link"
                  icon={<TeamOutlined />}
                  onClick={() => viewRolesWithPermission(permission)}
                >
                  View roles
                </Button>,
              ]}
            >
              <Meta
                title={formatPermissionId(permission)}
                description={PERMISSION_DESCRIPTIONS[permission] ?? ''}
              />
            </Card>
          ))}
        </Flex>
      )}
    </>
  );
}

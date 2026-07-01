import { useState } from 'react';
import {
  Button,
  Dropdown,
  Flex,
  Input,
  Result,
  Select,
  Spin,
  Table,
  type TableProps,
  Tag,
} from 'antd';
import { MoreOutlined, PlusOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import {
  useCan,
  useListPermissions,
  useSearchResourceGrants,
} from '../../domain/auth/auth.hooks.ts';
import {
  ResourceType,
  type SearchResourceGrantsQuery,
} from '../../services/graphql/graphql.ts';
import { useDebounced } from '../../commons/hooks.ts';
import { matchOption, orNull } from '../../commons/utils.ts';
import AssignAppRoleModal from './AssignAppRoleModal.tsx';
import RevokeAppRoleModal from './RevokeAppRoleModal.tsx';

const APP_RESOURCE = { type: ResourceType.App, id: '*' };
const PAGE_SIZE = 20;

type GrantRow =
  SearchResourceGrantsQuery['searchResourceGrants']['items'][number];

export default function AppTab() {
  const [assignOpen, setAssignOpen] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<GrantRow | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const username = searchParams.get('username') ?? '';
  const displayName = searchParams.get('displayName') ?? '';
  const roleName = searchParams.get('roleName') ?? '';
  const permission = searchParams.get('permission') ?? '';
  const scope = searchParams.get('scope') ?? '';
  const page = Number(searchParams.get('page')) || 0;

  // A filter change resets pagination; page changes keep the filters.
  const setFilter = (key: string) => (value: string) =>
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (value) next.set(key, value);
        else next.delete(key);
        next.delete('page');
        return next;
      },
      { replace: true },
    );
  const setPage = (next: number) =>
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev);
        if (next > 0) params.set('page', String(next));
        else params.delete('page');
        return params;
      },
      { replace: true },
    );

  const debUsername = useDebounced(username);
  const debDisplayName = useDebounced(displayName);
  const debRoleName = useDebounced(roleName);
  const debPermission = useDebounced(permission);
  const debScope = useDebounced(scope);

  const { isAllowed, isLoading: isLoadingCan } = useCan(
    APP_RESOURCE,
    'acl:list',
  );
  const { isAllowed: canAssign } = useCan(APP_RESOURCE, 'acl:add');
  const { isAllowed: canRevoke } = useCan(APP_RESOURCE, 'acl:remove');

  const { data, isLoading } = useSearchResourceGrants(
    {
      resourceType: ResourceType.App,
      resourceId: '*',
      pagination: { page, pageSize: PAGE_SIZE },
      filter: {
        username: orNull(debUsername),
        displayName: orNull(debDisplayName),
        roleName: orNull(debRoleName),
        permission: orNull(debPermission),
        scope: debScope ? (debScope as ResourceType) : null,
      },
    },
    isAllowed,
  );

  const { data: permsData } = useListPermissions('', isAllowed);
  const permissionOptions = [...(permsData?.listPermissions.permissions ?? [])]
    .sort()
    .map((p) => ({ value: p }));
  const scopeOptions = Object.entries(ResourceType).map(([label, value]) => ({
    label,
    value,
  }));

  const onChange = (p: number) => setPage(p - 1);

  if (isLoadingCan) return <Spin />;
  if (!isAllowed)
    return (
      <Result
        status="403"
        title="You don't have permission to view app access"
      />
    );

  const columns: TableProps<GrantRow>['columns'] = [
    {
      title: 'Username',
      dataIndex: ['user', 'username'],
      key: 'username',
    },
    {
      title: 'Display name',
      dataIndex: ['user', 'displayName'],
      key: 'displayName',
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'Roles',
      key: 'roles',
      render: (_, row) => (
        <Flex gap={4} wrap>
          {[...row.grants]
            .sort((a, b) => a.role.name.localeCompare(b.role.name))
            .map((g) => (
              <Tag key={g.role.id}>{g.role.name}</Tag>
            ))}
        </Flex>
      ),
    },
    ...(canRevoke
      ? [
          {
            title: 'Actions',
            key: 'actions',
            width: 64,
            render: (_: unknown, row: GrantRow) => (
              <Dropdown
                trigger={['click']}
                menu={{
                  items: [
                    {
                      key: 'revoke',
                      label: 'Revoke role',
                      danger: true,
                      onClick: () => setRevokeTarget(row),
                    },
                  ],
                }}
              >
                <Button type="text" icon={<MoreOutlined />} />
              </Dropdown>
            ),
          },
        ]
      : []),
  ];

  return (
    <>
      <Flex justify="space-between" align="start" style={{ marginBottom: 16 }}>
        <Flex gap={12} wrap>
          <Input
            placeholder="Username"
            allowClear
            value={username}
            onChange={(e) => setFilter('username')(e.target.value)}
            style={{ width: 160 }}
          />
          <Input
            placeholder="Display name"
            allowClear
            value={displayName}
            onChange={(e) => setFilter('displayName')(e.target.value)}
            style={{ width: 160 }}
          />
          <Input
            placeholder="Role name"
            allowClear
            value={roleName}
            onChange={(e) => setFilter('roleName')(e.target.value)}
            style={{ width: 160 }}
          />
          <Select
            placeholder="Permission"
            allowClear
            value={permission || undefined}
            options={permissionOptions}
            onChange={(v) => setFilter('permission')(v ?? '')}
            showSearch={{ filterOption: matchOption }}
            style={{ width: 200 }}
          />
          <Select
            placeholder="Role scope"
            allowClear
            value={scope || undefined}
            options={scopeOptions}
            onChange={(v) => setFilter('scope')(v ?? '')}
            style={{ width: 160 }}
          />
        </Flex>
        {canAssign && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAssignOpen(true)}
          >
            Assign role
          </Button>
        )}
      </Flex>
      <Table<GrantRow>
        rowKey={(row) => row.user.id}
        columns={columns}
        dataSource={data?.searchResourceGrants.items ?? []}
        loading={isLoading}
        pagination={{
          current: page + 1,
          pageSize: PAGE_SIZE,
          total: data?.searchResourceGrants.total ?? 0,
          showSizeChanger: false,
          onChange,
        }}
      />
      <AssignAppRoleModal
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
      />
      <RevokeAppRoleModal
        key={revokeTarget?.user.id ?? 'none'}
        target={revokeTarget}
        onClose={() => setRevokeTarget(null)}
      />
    </>
  );
}

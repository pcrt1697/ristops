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
import {
  useCan,
  useListPermissions,
  useSearchResourceGrants,
} from '../../domain/auth/auth.hooks.ts';
import {
  ResourceType,
  type SearchResourceGrantsQuery,
} from '../../services/graphql/graphql.ts';
import { useDebounced, useSearchParamFilters } from '../../commons/hooks.ts';
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
  const { get, setFilter, page, setPage } = useSearchParamFilters();

  const username = get('username');
  const displayName = get('displayName');
  const roleName = get('roleName');
  const permission = get('permission');

  const debUsername = useDebounced(username);
  const debDisplayName = useDebounced(displayName);
  const debRoleName = useDebounced(roleName);
  const debPermission = useDebounced(permission);

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
      },
    },
    isAllowed,
  );

  const { data: permsData } = useListPermissions('', isAllowed);
  const permissionOptions = [...(permsData?.listPermissions.permissions ?? [])]
    .sort()
    .map((p) => ({ value: p }));
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
                arrow
                trigger={['click']}
                placement="bottomRight"
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

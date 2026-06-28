import { useState } from 'react';
import {
  Button,
  Dropdown,
  Flex,
  Input,
  Popconfirm,
  Result,
  Select,
  Spin,
  Table,
  type TableProps,
  Tag,
  Typography,
} from 'antd';
import { MoreOutlined, PlusOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import {
  useCan,
  useListPermissions,
  useRevokeAccess,
  useSearchResourceGrants,
} from '../../domain/auth/auth.hooks.ts';
import {
  ResourceType,
  type SearchResourceGrantsQuery,
} from '../../services/graphql/graphql.ts';
import { useDebounced } from '../../commons/hooks.ts';
import { matchOption, orNull } from '../../commons/utils.ts';
import { message } from 'antd';
import AssignRoleModal from './AssignRoleModal.tsx';

const APP_RESOURCE = { type: ResourceType.App, id: '*' };
const PAGE_SIZE = 20;

type GrantRow =
  SearchResourceGrantsQuery['searchResourceGrants']['items'][number];

export default function AppTab() {
  const [assignOpen, setAssignOpen] = useState(false);
  // Which row's actions dropdown is open; kept controlled so the nested Popconfirm
  // can open without the menu closing on item click.
  const [openMenuUserId, setOpenMenuUserId] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const username = searchParams.get('username') ?? '';
  const displayName = searchParams.get('displayName') ?? '';
  const roleName = searchParams.get('roleName') ?? '';
  const permission = searchParams.get('permission') ?? '';
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

  const { isAllowed, isLoading: isLoadingCan } = useCan(APP_RESOURCE, 'acl:list');
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
  const permissionOptions = (permsData?.listPermissions.permissions ?? []).map(
    (p) => ({ value: p }),
  );

  const revoke = useRevokeAccess();
  const handleRevoke = (targetUserId: string, roleId: string) =>
    revoke.mutate(
      {
        userId: targetUserId,
        roleId,
        resourceType: ResourceType.App,
        resourceId: '*',
      },
      {
        onSuccess: () => void message.success('Access revoked'),
        onError: () => void message.error('Failed to revoke access'),
      },
    );

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
          {row.grants.map((g) => (
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
                open={openMenuUserId === row.user.id}
                onOpenChange={(open) =>
                  setOpenMenuUserId(open ? row.user.id : null)
                }
                menu={{
                  items: row.grants.map((g) => ({
                    key: g.role.id,
                    label: (
                      <Popconfirm
                        title="Revoke role"
                        description={`Revoke "${g.role.name}" from this user?`}
                        okText="Revoke"
                        okButtonProps={{ danger: true }}
                        onConfirm={() => {
                          handleRevoke(row.user.id, g.role.id);
                          setOpenMenuUserId(null);
                        }}
                      >
                        <Typography.Text
                          type="danger"
                          style={{ display: 'block' }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          Revoke {g.role.name}
                        </Typography.Text>
                      </Popconfirm>
                    ),
                  })),
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
          onChange: (p) => setPage(p - 1),
        }}
      />
      <AssignRoleModal
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
      />
    </>
  );
}

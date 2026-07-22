import { useState } from 'react';
import {
  Button,
  Flex,
  Input,
  message,
  Result,
  Spin,
  Switch,
  Table,
  type TableProps,
  Tag,
  Tooltip,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import {
  useCan,
  useRevokeAccess,
  useSearchResourceGrants,
} from '../../domain/auth/auth.hooks.ts';
import {
  ResourceType,
  type SearchResourceGrantsQuery,
} from '../../services/graphql/graphql.ts';
import { useDebounced, useSearchParamFilters } from '../../commons/hooks.ts';
import { orNull } from '../../commons/utils.ts';
import AssignVenueRoleModal from '../../components/venue/AssignVenueRoleModal.tsx';
import RoleDetailDrawer from '../../components/acl/RoleDetailDrawer.tsx';

const PAGE_SIZE = 20;

type GrantRow =
  SearchResourceGrantsQuery['searchResourceGrants']['items'][number];
type Grant = GrantRow['grants'][number];

interface Selected {
  userId: string;
  grant: Grant;
}

export default function VenueStaffPage() {
  const { venueId = '' } = useParams<{ venueId: string }>();
  const [assignOpen, setAssignOpen] = useState(false);
  const [selected, setSelected] = useState<Selected | null>(null);
  const { get, setFilter, page, setPage } = useSearchParamFilters();

  const venue = { type: ResourceType.Venue, id: venueId };
  const { isAllowed, isLoading: isLoadingCan } = useCan(venue, 'acl:list');
  const { isAllowed: isAppLevel } = useCan(
    { type: ResourceType.App, id: '*' },
    'acl:list',
  );
  const { isAllowed: canAssign } = useCan(venue, 'acl:add');
  const { isAllowed: canRevoke } = useCan(venue, 'acl:remove');

  const username = get('username');
  const displayName = get('displayName');
  const roleName = get('roleName');
  const hideInherited = get('hideInherited') === '1';

  const debUsername = useDebounced(username);
  const debDisplayName = useDebounced(displayName);
  const debRoleName = useDebounced(roleName);

  // Venue managers (not app-level) never see inherited app roles — the list is scoped
  // to venue roles and inherited tags are hidden. App-level viewers can toggle it.
  const onlyVenueScope = !isAppLevel || hideInherited;

  const revoke = useRevokeAccess();

  const { data, isLoading } = useSearchResourceGrants(
    {
      resourceType: ResourceType.Venue,
      resourceId: venueId,
      pagination: { page, pageSize: PAGE_SIZE },
      filter: {
        username: orNull(debUsername),
        displayName: orNull(debDisplayName),
        roleName: orNull(debRoleName),
        scope: onlyVenueScope ? ResourceType.Venue : null,
      },
    },
    isAllowed,
  );

  const isInherited = (grant: Grant) =>
    !(
      grant.resource.resourceType === ResourceType.Venue &&
      grant.resource.resourceId === venueId
    );

  const handleRevoke = () => {
    if (!selected) return;
    revoke.mutate(
      {
        userId: selected.userId,
        roleId: selected.grant.role.id,
        resourceType: ResourceType.Venue,
        resourceId: venueId,
      },
      {
        onSuccess: () => {
          void message.success('Role revoked');
          setSelected(null);
        },
        onError: () => void message.error('Failed to revoke role'),
      },
    );
  };

  if (isLoadingCan) return <Spin />;
  if (!isAllowed)
    return (
      <Result
        status="403"
        title="You don't have permission to view venue staff"
      />
    );

  const columns: TableProps<GrantRow>['columns'] = [
    { title: 'Username', dataIndex: ['user', 'username'], key: 'username' },
    {
      title: 'Display name',
      dataIndex: ['user', 'displayName'],
      key: 'displayName',
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'Roles',
      key: 'roles',
      render: (_, row) => {
        const grants = onlyVenueScope
          ? row.grants.filter((g) => !isInherited(g))
          : row.grants;
        return (
          <Flex gap={4} wrap>
            {[...grants]
              .sort((a, b) => a.role.name.localeCompare(b.role.name))
              .map((grant) => {
                const inherited = isInherited(grant);
                const title = inherited
                  ? 'Inherited from app'
                  : grant.expiresAt
                    ? `Expires ${new Date(grant.expiresAt).toLocaleString()}`
                    : undefined;
                const tag = (
                  <Tag
                    color={inherited ? 'default' : 'blue'}
                    style={{ cursor: 'pointer' }}
                    onClick={() =>
                      setSelected({ userId: row.user.id, grant })
                    }
                  >
                    {grant.role.name}
                    {grant.expiresAt ? ' ⏳' : ''}
                  </Tag>
                );
                return (
                  <span key={grant.role.id}>
                    {title ? <Tooltip title={title}>{tag}</Tooltip> : tag}
                  </span>
                );
              })}
          </Flex>
        );
      },
    },
  ];

  return (
    <>
      <Flex justify="space-between" align="start" style={{ marginBottom: 16 }}>
        <Flex gap={12} wrap align="center">
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
          {isAppLevel && (
            <Flex gap={8} align="center">
              <Switch
                checked={hideInherited}
                onChange={(v) => setFilter('hideInherited')(v ? '1' : '')}
              />
              Hide inherited
            </Flex>
          )}
        </Flex>
        {canAssign && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAssignOpen(true)}
          >
            Add staff
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
      <AssignVenueRoleModal
        venueId={venueId}
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
      />
      <RoleDetailDrawer
        key={selected ? `${selected.userId}:${selected.grant.role.id}` : 'none'}
        role={selected?.grant.role ?? null}
        grant={
          selected
            ? {
                inherited: isInherited(selected.grant),
                expiresAt: selected.grant.expiresAt,
                canRevoke: canRevoke && !isInherited(selected.grant),
                revoking: revoke.isPending,
                onRevoke: handleRevoke,
              }
            : undefined
        }
        onClose={() => setSelected(null)}
      />
    </>
  );
}

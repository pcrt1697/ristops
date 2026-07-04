import { useState } from 'react';
import { DatePicker, Flex, Form, message, Modal, Select, Typography } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import {
  useGrantAccess,
  useListRoles,
  useSearchMembers,
} from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useDebounced } from '../../commons/hooks.ts';
import { matchOption } from '../../commons/utils.ts';
import RoleDetails from '../acl/RoleDetails.tsx';

const { Text } = Typography;

interface AssignVenueRoleModalProps {
  venueId: string;
  open: boolean;
  onClose: () => void;
}

export default function AssignVenueRoleModal({
  venueId,
  open,
  onClose,
}: AssignVenueRoleModalProps) {
  const [userId, setUserId] = useState<string>();
  const [roleId, setRoleId] = useState<string>();
  const [expiresAt, setExpiresAt] = useState<Dayjs | null>(null);
  const [userSearch, setUserSearch] = useState('');
  const debouncedUserSearch = useDebounced(userSearch);

  const { data: membersData } = useSearchMembers(
    {
      pagination: { page: 0, pageSize: 20 },
      sort: [],
      filter: { username: debouncedUserSearch || null },
    },
    open,
  );
  const { data: rolesData } = useListRoles({ scope: ResourceType.Venue }, open);
  const grant = useGrantAccess();

  const memberOptions = (membersData?.searchMembers.items ?? []).map((m) => ({
    value: m.id,
    label: m.displayName ? `${m.displayName} (${m.username})` : m.username,
  }));
  const roles = rolesData?.listRoles.roles ?? [];
  const roleOptions = roles.map((r) => ({
    value: r.id,
    label: r.name,
    description: r.description,
  }));
  const selectedRole = roles.find((r) => r.id === roleId);

  const reset = () => {
    setUserId(undefined);
    setRoleId(undefined);
    setExpiresAt(null);
    setUserSearch('');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleOk = () => {
    if (!userId || !roleId) return;
    grant.mutate(
      {
        userId,
        roleId,
        resourceType: ResourceType.Venue,
        resourceId: venueId,
        expiresAt: expiresAt ? expiresAt.toISOString() : null,
      },
      {
        onSuccess: () => {
          void message.success('Role assigned');
          handleClose();
        },
        onError: () => void message.error('Failed to assign role'),
      },
    );
  };

  return (
    <Modal
      title="Add staff"
      open={open}
      onOk={handleOk}
      onCancel={handleClose}
      okText="Assign"
      okButtonProps={{ disabled: !userId || !roleId, loading: grant.isPending }}
    >
      <Form layout="vertical">
        <Form.Item label="User">
          <Select
            placeholder="Search user by username"
            value={userId}
            options={memberOptions}
            onSearch={setUserSearch}
            onChange={setUserId}
            showSearch={{ filterOption: false }}
            notFoundContent={null}
            style={{ width: '100%' }}
          />
        </Form.Item>
        <Form.Item label="Role">
          <Select
            placeholder="Select a role"
            value={roleId}
            options={roleOptions}
            onChange={setRoleId}
            optionRender={(option) => (
              <Flex vertical>
                <Text>{option.data.label}</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {option.data.description}
                </Text>
              </Flex>
            )}
            showSearch={{ filterOption: matchOption }}
            style={{ width: '100%' }}
          />
        </Form.Item>
        {selectedRole && (
          <Form.Item>
            <RoleDetails
              description={selectedRole.description}
              permissions={selectedRole.permissions}
            />
          </Form.Item>
        )}
        <Form.Item label="Expires at" help="Leave empty for a permanent grant">
          <DatePicker
            showTime
            value={expiresAt}
            onChange={setExpiresAt}
            disabledDate={(d) => d.isBefore(dayjs(), 'day')}
            style={{ width: '100%' }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}

import { useState } from 'react';
import { Form, message, Modal, Select } from 'antd';
import {
  useGrantAccess,
  useListRoles,
  useSearchMembers,
} from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useDebounced } from '../../commons/hooks.ts';
import { matchOption } from '../../commons/utils.ts';

interface AssignRoleModalProps {
  open: boolean;
  onClose: () => void;
}

export default function AssignRoleModal({ open, onClose }: AssignRoleModalProps) {
  const [userId, setUserId] = useState<string>();
  const [roleId, setRoleId] = useState<string>();
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
  const { data: rolesData } = useListRoles({}, open);
  const grant = useGrantAccess();

  const memberOptions = (membersData?.searchMembers.items ?? []).map((m) => ({
    value: m.id,
    label: m.displayName ? `${m.displayName} (${m.username})` : m.username,
  }));
  const roleOptions = (rolesData?.listRoles.roles ?? []).map((r) => ({
    value: r.id,
    label: r.name,
  }));

  const reset = () => {
    setUserId(undefined);
    setRoleId(undefined);
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
        resourceType: ResourceType.App,
        resourceId: '*',
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
      title="Assign role on app"
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
            showSearch={{ filterOption: matchOption }}
            style={{ width: '100%' }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}

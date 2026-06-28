import { useState } from 'react';
import { Form, message, Modal, Select } from 'antd';
import { useRevokeAccess } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';

interface RevokeTarget {
  user: { id: string; username: string };
  grants: { role: { id: string; name: string } }[];
}

interface RevokeAppRoleModalProps {
  target: RevokeTarget | null;
  onClose: () => void;
}

export default function RevokeAppRoleModal({
  target,
  onClose,
}: RevokeAppRoleModalProps) {
  const [roleId, setRoleId] = useState<string>();
  const revoke = useRevokeAccess();

  const roleOptions = (target?.grants ?? []).map((g) => ({
    value: g.role.id,
    label: g.role.name,
  }));

  const handleOk = () => {
    if (!target || !roleId) return;
    revoke.mutate(
      {
        userId: target.user.id,
        roleId,
        resourceType: ResourceType.App,
        resourceId: '*',
      },
      {
        onSuccess: () => {
          void message.success('App role revoked');
          onClose();
        },
        onError: () => void message.error('Failed to revoke app role'),
      },
    );
  };

  return (
    <Modal
      title={
        target
          ? `Revoke app role for ${target.user.username}`
          : 'Revoke app role'
      }
      open={target !== null}
      onOk={handleOk}
      onCancel={onClose}
      okText="Revoke"
      okButtonProps={{
        danger: true,
        disabled: !roleId,
        loading: revoke.isPending,
      }}
    >
      <Form layout="vertical">
        <Form.Item label="Role to revoke">
          <Select
            placeholder="Select a role"
            value={roleId}
            options={roleOptions}
            onChange={setRoleId}
            style={{ width: '100%' }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}

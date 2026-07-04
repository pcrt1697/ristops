import { useState } from 'react';
import { Button, Divider, Drawer, Flex, Typography } from 'antd';
import type { ResourceType } from '../../services/graphql/graphql.ts';
import RoleDetails from './RoleDetails.tsx';
import RoleScopeTag from './RoleScopeTag.tsx';

const { Text } = Typography;

interface RoleLike {
  name: string;
  description: string;
  permissions: string[];
  scope: ResourceType;
}

export interface GrantContext {
  inherited: boolean;
  expiresAt?: string | null;
  canRevoke: boolean;
  revoking?: boolean;
  onRevoke: () => void;
}

interface RoleDetailDrawerProps {
  role: RoleLike | null;
  /** When present, the drawer describes a user's grant of this role and offers revoke. */
  grant?: GrantContext;
  onClose: () => void;
}

/** Shows a role's description + permissions; optionally the grant context with inline revoke. */
export default function RoleDetailDrawer({
  role,
  grant,
  onClose,
}: RoleDetailDrawerProps) {
  const [confirming, setConfirming] = useState(false);

  const close = () => {
    setConfirming(false);
    onClose();
  };

  return (
    <Drawer
      title={
        role && (
          <Flex align="center" gap={8}>
            <span>{role.name}</span>
            <RoleScopeTag scope={role.scope} />
          </Flex>
        )
      }
      open={role !== null}
      onClose={close}
      size={360}
    >
      {role && (
        <Flex vertical gap={16}>
          <RoleDetails
            description={role.description}
            permissions={role.permissions}
          />
          {grant && (
            <>
              <Divider style={{ margin: 0 }} />
              {grant.inherited ? (
                <Text type="secondary">
                  Inherited from the app — cannot be revoked here.
                </Text>
              ) : (
                <Flex vertical gap={8}>
                  {grant.expiresAt && (
                    <Text type="secondary">
                      Expires {new Date(grant.expiresAt).toLocaleString()}
                    </Text>
                  )}
                  {grant.canRevoke &&
                    (confirming ? (
                      <Flex gap={8} align="center">
                        <Text>Revoke this role?</Text>
                        <Button
                          danger
                          size="small"
                          loading={grant.revoking}
                          onClick={grant.onRevoke}
                        >
                          Revoke
                        </Button>
                        <Button
                          size="small"
                          onClick={() => setConfirming(false)}
                        >
                          Cancel
                        </Button>
                      </Flex>
                    ) : (
                      <Button danger onClick={() => setConfirming(true)}>
                        Revoke role
                      </Button>
                    ))}
                </Flex>
              )}
            </>
          )}
        </Flex>
      )}
    </Drawer>
  );
}

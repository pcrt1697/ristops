import { Card, Flex, Typography } from 'antd';
import {
  formatPermissionId,
  PERMISSION_DESCRIPTIONS,
} from '../../domain/auth/permissions.ts';

const { Meta } = Card;
const { Text, Title } = Typography;

function PermissionRow({ id }: { id: string }) {
  return (
    <Card size="small">
      <Meta
        title={id}
        description={PERMISSION_DESCRIPTIONS[id] ?? formatPermissionId(id)}
      />
    </Card>
  );
}

interface RoleDetailsProps {
  description: string;
  permissions: string[];
}

/** Shared "what does this role mean" view: description + its permissions. */
export default function RoleDetails({
  description,
  permissions,
}: RoleDetailsProps) {
  return (
    <Flex vertical gap={8}>
      <Text type="secondary">{description}</Text>
      <Title level={5} style={{ marginBottom: 0 }}>
        Permissions
      </Title>
      <Flex vertical gap={4}>
        {[...permissions].sort().map((p) => (
          <PermissionRow key={p} id={p} />
        ))}
      </Flex>
    </Flex>
  );
}

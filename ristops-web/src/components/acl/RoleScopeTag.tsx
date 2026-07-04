import { Tag } from 'antd';
import type { ResourceType } from '../../services/graphql/graphql.ts';
import { formatScope } from '../../domain/auth/authz.utils.ts';

/** Badge for a role's scope (resource type), shown next to the role name. */
export default function RoleScopeTag({ scope }: { scope: ResourceType }) {
  return (
    <Tag color="blue" style={{ margin: 0 }}>
      {formatScope(scope)}
    </Tag>
  );
}

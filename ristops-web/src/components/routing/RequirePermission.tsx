import { type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { Result, Spin } from 'antd';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import type { ResourceType } from '../../services/graphql/graphql.ts';

type AppResource =
  | { type: ResourceType; id: string }
  | { type: ResourceType; fromParam: string };

interface RequirePermissionProps {
  resource: AppResource;
  permissions: string[];
  children: ReactNode;
}

export default function RequirePermission({
  permissions,
  resource,
  children,
}: RequirePermissionProps) {
  const params = useParams();

  const resourceId =
    'id' in resource ? resource.id : params[resource.fromParam];

  if (resourceId === undefined) {
    throw new Error(
      `RequirePermission: param "${(resource as { fromParam: string }).fromParam}" is not present in the current route.`,
    );
  }

  const { isAllowed, isLoading } = useCan(
    { type: resource.type, id: resourceId },
    ...permissions,
  );

  if (isLoading) return <Spin fullscreen />;
  if (!isAllowed)
    return (
      <Result
        status="403"
        title="403"
        subTitle="You don't have permission to access this page."
      />
    );

  return <>{children}</>;
}

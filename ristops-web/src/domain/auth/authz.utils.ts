import type { UserRoleGrant } from '../../services/graphql/graphql.ts';

export function matchesPermission(granted: string, requested: string): boolean {
  if (granted === '*') return true;
  if (granted === requested) return true;
  const scope = requested.split('~')[0];
  return granted === `${scope}~*`;
}

export function hasPermission(
  grants: UserRoleGrant[],
  permission: string,
): boolean {
  return grants.some((grant) =>
    grant.role.permissions.some((p) => matchesPermission(p, permission)),
  );
}

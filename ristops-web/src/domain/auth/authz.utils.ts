import type { UserRoleGrant } from '../../services/graphql/graphql.ts';
import { PERMISSION_SEPARATOR } from './permissions.ts';

export function matchesPermission(granted: string, requested: string): boolean {
  if (granted === '*') return true;
  if (granted === requested) return true;
  const scope = requested.split(PERMISSION_SEPARATOR)[0];
  return granted === `${scope}${PERMISSION_SEPARATOR}*`;
}

export function hasPermission(
  grants: UserRoleGrant[],
  permission: string,
): boolean {
  return grants.some((grant) =>
    grant.role.permissions.some((p) => matchesPermission(p, permission)),
  );
}

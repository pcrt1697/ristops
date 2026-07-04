import type { UserRoleGrant } from '../../services/graphql/graphql.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { PERMISSION_SEPARATOR } from './permissions.ts';

/**
 * Resource types a role can actually be scoped to. This is a deliberate subset
 * of `ResourceType` (roles are never scoped to ACL/PERMISSION/ROLE), so filters
 * should offer these rather than the full enum.
 */
export const ROLE_SCOPES: ResourceType[] = [
  ResourceType.App,
  ResourceType.User,
  ResourceType.Venue,
];

/** Human-readable label for a role scope (resource type), e.g. VENUE -> "Venue". */
export function formatScope(scope: ResourceType): string {
  return scope.charAt(0) + scope.slice(1).toLowerCase();
}

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

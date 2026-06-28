/** Separator between a permission's scope and action (e.g. "venue:add"). */
export const PERMISSION_SEPARATOR = ':';

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function formatPermissionId(id: string): string {
  if (id === '*') return 'All permissions';
  const [resource, action] = id.split(PERMISSION_SEPARATOR);
  return `${capitalize(resource)}: ${capitalize(action)}`;
}

export const PERMISSION_DESCRIPTIONS: Record<string, string> = {
  'venue:list':      'Browse and search all venues',
  'venue:add':       'Create new venues',
  'venue:get':       'View venue details',
  'venue:edit':      'Edit venue details',
  'venue:remove':    'Delete venues',
  'user:get':        'View user profiles',
  'user:edit':       'Edit user details',
  'user:remove':     'Remove users',
  'role:get':        'View role details',
  'role:list':       'Browse the role catalog',
  'permission:list': 'Browse available permissions',
  'acl:get':         'View access grants',
  'acl:list':        'List access grants on a resource',
  'acl:add':         'Grant roles to users',
  'acl:remove':      'Revoke roles from users',
  'resource:add':    'Create resources',
  'resource:remove': 'Delete resources',
  'resource:list':   'Browse resources',
  '*':               'Unrestricted access to all operations',
};

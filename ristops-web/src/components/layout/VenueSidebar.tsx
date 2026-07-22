import { type MenuProps } from 'antd';
import {
  AppstoreOutlined,
  HomeOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import Sidebar from './Sidebar.tsx';

export default function VenueSidebar({ venueId }: { venueId: string }) {
  const navigate = useNavigate();
  const resource = { type: ResourceType.Venue, id: venueId };
  // TODO: this is a temporary flag
  //  for the future: if a user has 'service:' permissions on a service and not on a venue,
  //  he would not be able to see the item
  const { isAllowed: canEditSettings } = useCan(
    resource,
    'venue:edit',
    'venue:activate',
    'venue:close',
    'venue:disable',
    'venue:enable',
    'service:add',
    'service:edit',
    'service:remove',
  );
  const { isAllowed: canManageServices } = useCan(
    resource,
    'service:list',
    'service:add',
    'service:edit',
    'service:remove',
  );
  const { isAllowed: canManageAcl } = useCan(resource, 'acl:list');

  const go = (path: string) => () => void navigate(path);

  const manageChildren: MenuProps['items'] = [];
  if (canEditSettings) {
    manageChildren.push({
      key: `/venues/${venueId}/settings`,
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: go(`/venues/${venueId}/settings`),
    });
  }
  if (canManageServices) {
    manageChildren.push({
      key: `/venues/${venueId}/services`,
      icon: <AppstoreOutlined />,
      label: 'Services',
      onClick: go(`/venues/${venueId}/services`),
    });
  }
  if (canManageAcl) {
    manageChildren.push({
      key: `/venues/${venueId}/staff`,
      icon: <TeamOutlined />,
      label: 'Staff',
      onClick: go(`/venues/${venueId}/staff`),
    });
  }

  const items: MenuProps['items'] = [
    {
      key: `/venues/${venueId}`,
      icon: <HomeOutlined />,
      label: 'Home',
      onClick: go(`/venues/${venueId}`),
    },
  ];
  if (manageChildren.length > 0) {
    items.push({
      key: 'manage',
      type: 'group',
      label: 'Manage',
      children: manageChildren,
    });
  }

  return <Sidebar items={items} />;
}

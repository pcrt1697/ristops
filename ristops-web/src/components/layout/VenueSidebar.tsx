import { type MenuProps } from 'antd';
import {
  AppstoreOutlined,
  CalendarOutlined,
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
  // Settings holds venue details, the lifecycle status card, and venue-wide closings — the last
  // of which authorizes against `schedule:*`. Only the write permissions count: `schedule:list`
  // is held by every role, and gating on it would put Settings back in front of staff who
  // cannot change anything on the page.
  const { isAllowed: canEditSettings } = useCan(
    resource,
    'venue:edit',
    'venue:activate',
    'venue:close',
    'venue:disable',
    'venue:enable',
    'schedule:add',
    'schedule:edit',
    'schedule:remove',
  );
  // TODO: this is a temporary flag
  //  for the future: if a user has 'service:' permissions on a service and not on a venue,
  //  he would not be able to see the item
  const { isAllowed: canManageServices } = useCan(
    resource,
    'service:list',
    'service:add',
    'service:edit',
    'service:remove',
  );
  const { isAllowed: canManageReservations } = useCan(
    resource,
    'reservation:list',
    'reservation:add',
  );
  const { isAllowed: canManageAcl } = useCan(resource, 'acl:list');

  const go = (path: string) => () => void navigate(path);

  // Split by what the user is doing, not by permission level: running the venue day to day
  // (which services are on, and who is booked into them) above administering it. Most roles —
  // server, bartender, chef — only ever hold the first group.
  const serviceChildren: MenuProps['items'] = [];
  if (canManageServices) {
    serviceChildren.push({
      key: `/venues/${venueId}/services`,
      icon: <AppstoreOutlined />,
      label: 'Services',
      onClick: go(`/venues/${venueId}/services`),
    });
  }
  if (canManageReservations) {
    serviceChildren.push({
      key: `/venues/${venueId}/reservations`,
      icon: <CalendarOutlined />,
      label: 'Reservations',
      onClick: go(`/venues/${venueId}/reservations`),
    });
  }

  const manageChildren: MenuProps['items'] = [];
  if (canManageAcl) {
    manageChildren.push({
      key: `/venues/${venueId}/staff`,
      icon: <TeamOutlined />,
      label: 'Staff',
      onClick: go(`/venues/${venueId}/staff`),
    });
  }
  if (canEditSettings) {
    manageChildren.push({
      key: `/venues/${venueId}/settings`,
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: go(`/venues/${venueId}/settings`),
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
  if (serviceChildren.length > 0) {
    items.push({
      key: 'service',
      type: 'group',
      label: 'Service',
      children: serviceChildren,
    });
  }
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

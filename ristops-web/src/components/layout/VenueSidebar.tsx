import { type MenuProps } from 'antd';
import {
  ClockCircleOutlined,
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
  const { isAllowed: canEdit } = useCan(resource, 'venue:edit');
  const { isAllowed: canRemove } = useCan(resource, 'venue:remove');
  const { isAllowed: canManageAcl } = useCan(resource, 'acl:list');

  const go = (path: string) => () => void navigate(path);

  const manageChildren: MenuProps['items'] = [];
  if (canEdit || canRemove) {
    manageChildren.push({
      key: `/venues/${venueId}/settings`,
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: go(`/venues/${venueId}/settings`),
    });
  }
  if (canEdit) {
    manageChildren.push({
      key: `/venues/${venueId}/schedule`,
      icon: <ClockCircleOutlined />,
      label: 'Schedule',
      onClick: go(`/venues/${venueId}/schedule`),
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

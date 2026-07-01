import { type MenuProps } from 'antd';
import { HomeOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import Sidebar from './Sidebar.tsx';

export default function VenueSidebar({ venueId }: { venueId: string }) {
  const navigate = useNavigate();
  const { isAllowed: canManageVenueAcl } = useCan(
    { type: ResourceType.Venue, id: venueId },
    'acl:list',
  );

  const items: MenuProps['items'] = [
    {
      key: `/venues/${venueId}`,
      icon: <HomeOutlined />,
      label: 'Home',
      onClick: () => void navigate(`/venues/${venueId}`),
    },
  ];
  if (canManageVenueAcl) {
    items.push({
      key: `/venues/${venueId}/access-control`,
      icon: <SafetyCertificateOutlined />,
      label: 'Access Control',
      onClick: () => void navigate(`/venues/${venueId}/access-control`),
    });
  }

  return <Sidebar items={items} />;
}

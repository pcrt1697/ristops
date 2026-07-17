import { useParams } from 'react-router-dom';
import { Descriptions, Space, Spin, Tag } from 'antd';
import { useVenue } from '../../domain/venue/venue.hooks.ts';
import { statusTagColor } from '../../domain/venue/venue.utils.ts';

export default function VenueHomePage() {
  const { venueId } = useParams<{ venueId: string }>();
  const { data, isLoading } = useVenue(venueId);
  const venue = data?.venue;

  if (isLoading) return <Spin />;
  if (!venue) return null;

  return (
    <Descriptions
      title={
        <Space>
          {venue.name}
          <Tag color={statusTagColor[venue.status]}>{venue.status}</Tag>
        </Space>
      }
      column={1}
    >
      <Descriptions.Item label="Address">{venue.address}</Descriptions.Item>
      <Descriptions.Item label="Description">
        {venue.description ?? '—'}
      </Descriptions.Item>
    </Descriptions>
  );
}

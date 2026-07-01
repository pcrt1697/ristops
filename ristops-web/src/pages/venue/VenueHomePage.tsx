import { useParams } from 'react-router-dom';
import { Descriptions, Spin } from 'antd';
import { useVenue } from '../../domain/venue/venue.hooks.ts';

export default function VenueHomePage() {
  const { venueId } = useParams<{ venueId: string }>();
  const { data, isLoading } = useVenue(venueId);
  const venue = data?.venue;

  if (isLoading) return <Spin />;
  if (!venue) return null;

  return (
    <Descriptions title={venue.name} column={1}>
      <Descriptions.Item label="Address">{venue.address}</Descriptions.Item>
      <Descriptions.Item label="Description">
        {venue.description ?? '—'}
      </Descriptions.Item>
    </Descriptions>
  );
}

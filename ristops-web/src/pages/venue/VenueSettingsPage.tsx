import { Spin } from 'antd';
import { useParams } from 'react-router-dom';
import { useVenue } from '../../domain/venue/venue.hooks.ts';
import VenueDetailsSection from '../../components/venue/VenueDetailsSection.tsx';
import VenueStatusCard from '../../components/venue/VenueStatusCard.tsx';
import ClosingsSection from '../../components/venue/ClosingsSection.tsx';

export default function VenueSettingsPage() {
  const { venueId = '' } = useParams<{ venueId: string }>();
  const { data: venueData, isLoading } = useVenue(venueId);
  const venue = venueData?.venue;

  if (isLoading) return <Spin />;
  if (!venue) return null;

  return (
    <>
      <VenueDetailsSection venue={venue} />
      <VenueStatusCard venue={venue} />
      <ClosingsSection venueId={venueId} />
    </>
  );
}

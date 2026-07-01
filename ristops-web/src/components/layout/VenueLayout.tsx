import { useEffect } from 'react';
import { Outlet, useParams } from 'react-router-dom';

import { useCurrentVenue } from '../../domain/venue/venue.hooks.ts';

export default function VenueLayout() {
  const { venueId } = useParams<{ venueId: string }>();
  const { currentVenueId, setCurrentVenueId } = useCurrentVenue();

  // Keep the current-venue context in sync when entering a venue directly by URL.
  useEffect(() => {
    if (venueId && venueId !== currentVenueId) setCurrentVenueId(venueId);
  }, [venueId, currentVenueId, setCurrentVenueId]);

  return <Outlet />;
}

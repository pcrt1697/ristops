import { useEffect } from 'react';
import { Outlet, useNavigate, useParams } from 'react-router-dom';
import { useCurrentVenue, useVenue } from '../../domain/venue/venue.hooks.ts';
import type { ServiceError } from '../../services/common.ts';

export default function VenueLayout() {
  const { venueId = '' } = useParams<{ venueId: string }>();
  const navigate = useNavigate();
  const { currentVenueId, setCurrentVenueId } = useCurrentVenue();
  const { error } = useVenue(venueId);
  const notFound = (error as ServiceError | null)?.status === 404;

  // Keep the current-venue context in sync with the URL. If the venue doesn't exist
  // (e.g. a stale link after a reseed), clear it and leave the venue section.
  useEffect(() => {
    if (notFound) {
      setCurrentVenueId(null);
      void navigate('/', { replace: true });
      return;
    }
    if (venueId && venueId !== currentVenueId) setCurrentVenueId(venueId);
  }, [venueId, currentVenueId, notFound, setCurrentVenueId, navigate]);

  return <Outlet />;
}

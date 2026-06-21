import { useParams } from 'react-router-dom';

export default function VenueLayout() {
  const { venueId } = useParams<{ venueId: string }>();
  return <div></div>;
}

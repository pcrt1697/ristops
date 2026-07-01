import { useState } from 'react';
import { Avatar, Card, Flex, Input, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  useCurrentVenue,
  useSearchVenues,
} from '../domain/venue/venue.hooks.ts';
import { useDebounced } from '../commons/hooks.ts';
import { initials, orNull } from '../commons/utils.ts';

const { Meta } = Card;
const { Search } = Input;

export default function HomePage() {
  const navigate = useNavigate();
  const { setCurrentVenueId } = useCurrentVenue();
  const [search, setSearch] = useState('');
  const debounced = useDebounced(search);

  const { data, isLoading } = useSearchVenues(
    { name: orNull(debounced) },
    { page: 0, pageSize: 20 },
  );
  const venues = data?.searchVenues.items ?? [];

  const selectVenue = (id: string) => {
    setCurrentVenueId(id);
    void navigate(`/venues/${id}`);
  };

  return (
    <Flex vertical gap={24}>
      <Search
        placeholder="Search venues"
        allowClear
        onChange={(e) => setSearch(e.target.value)}
        style={{ maxWidth: 320 }}
      />
      {isLoading ? (
        <Spin />
      ) : (
        <Flex wrap gap={16}>
          {venues.map((venue) => (
            <Card
              key={venue.id}
              hoverable
              style={{ width: 280 }}
              onClick={() => selectVenue(venue.id)}
            >
              <Meta
                avatar={<Avatar>{initials(venue.name)}</Avatar>}
                title={venue.name}
                description={venue.address}
              />
            </Card>
          ))}
        </Flex>
      )}
    </Flex>
  );
}

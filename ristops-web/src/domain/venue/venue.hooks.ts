import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import type {
  PaginationInput,
  VenueFilterInput,
  VenueSortFieldSortInput,
} from '../../services/graphql/graphql.ts';
import { venueApi } from './venue.api.ts';

export function useSearchVenues(
  filter?: VenueFilterInput,
  pagination?: PaginationInput,
  sort?: VenueSortFieldSortInput[],
) {
  return useQuery({
    queryKey: ['venue.search', filter, pagination, sort],
    queryFn: () => venueApi.searchVenues(filter, pagination, sort),
  });
}

export function useCreateVenue() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: venueApi.createVenue,
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ['venue.search'] });
      void navigate(`/venues/${data.createVenue.id}`);
    },
    onError: () => {
      void message.error('Could not create the venue');
    },
  });
}

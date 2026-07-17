import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import type {
  PaginationInput,
  UpdateVenueInput,
  VenueFilterInput,
  VenueSortFieldSortInput,
} from '../../services/graphql/graphql.ts';
import { venueApi } from './venue.api.ts';
import {
  type CurrentVenueContextValue,
  VenueContext,
} from './venue.context.ts';
import { use } from 'react';

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

export function useVenue(id: string | null | undefined) {
  return useQuery({
    queryKey: ['venue.get', id],
    queryFn: () => venueApi.getVenue(id as string),
    enabled: !!id,
    retry: false,
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

export function useUpdateVenue(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: UpdateVenueInput) => venueApi.updateVenue(id, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['venue.get', id] });
      void queryClient.invalidateQueries({ queryKey: ['venue.search'] });
    },
    onError: () => {
      void message.error('Could not update the venue');
    },
  });
}

// Status actions (activate/close/disable/enable) never remove the venue or drop it from
// context — unlike the old hard-delete, CLOSED preserves everything so the owner can reopen.
// So these just invalidate the cache, matching useUpdateVenue's pattern, not useDeleteVenue's.

export function useActivateVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => venueApi.activateVenue(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey: ['venue.get', id] });
      void queryClient.invalidateQueries({ queryKey: ['venue.search'] });
    },
    onError: () => {
      void message.error('Could not activate the venue');
    },
  });
}

export function useCloseVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => venueApi.closeVenue(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey: ['venue.get', id] });
      void queryClient.invalidateQueries({ queryKey: ['venue.search'] });
    },
    onError: () => {
      void message.error('Could not close the venue');
    },
  });
}

export function useDisableVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => venueApi.disableVenue(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey: ['venue.get', id] });
      void queryClient.invalidateQueries({ queryKey: ['venue.search'] });
    },
    onError: () => {
      void message.error('Could not disable the venue');
    },
  });
}

export function useEnableVenue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => venueApi.enableVenue(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey: ['venue.get', id] });
      void queryClient.invalidateQueries({ queryKey: ['venue.search'] });
    },
    onError: () => {
      void message.error('Could not enable the venue');
    },
  });
}

export function useCurrentVenue(): CurrentVenueContextValue {
  const ctx = use(VenueContext);
  if (!ctx)
    throw new Error('useCurrentVenue must be used within CurrentVenueProvider');
  return ctx;
}

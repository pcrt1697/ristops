import {
  CreateVenueDocument,
  type CreateVenueInput,
  DeleteVenueDocument,
  GetVenueDocument,
  type PaginationInput,
  SearchVenuesDocument,
  UpdateVenueDocument,
  type UpdateVenueInput,
  type VenueFilterInput,
  type VenueSortFieldSortInput,
} from '../../services/graphql/graphql.ts';
import { gqlRequest } from '../../services/graphql/client.ts';

export const venueApi = {
  getVenue: (id: string) => gqlRequest(GetVenueDocument, { id }),
  searchVenues: (
    filter?: VenueFilterInput,
    pagination?: PaginationInput,
    sort?: VenueSortFieldSortInput[],
  ) =>
    gqlRequest(SearchVenuesDocument, { input: { filter, pagination, sort } }),
  createVenue: (input: CreateVenueInput) =>
    gqlRequest(CreateVenueDocument, { input }),
  updateVenue: (id: string, input: UpdateVenueInput) =>
    gqlRequest(UpdateVenueDocument, { id, input }),
  deleteVenue: (id: string) => gqlRequest(DeleteVenueDocument, { id }),
};

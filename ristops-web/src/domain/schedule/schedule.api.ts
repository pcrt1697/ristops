import { collectAllPages } from '../../commons/utils.ts';
import { gqlRequest } from '../../services/graphql/client.ts';
import {
  type ClosingCreateInput,
  type ClosingSearchInput,
  type ClosingUpdateInput,
  CreateClosingDocument,
  DeleteClosingDocument,
  ListServiceOpeningsDocument,
  type OpeningUpsertInput,
  SearchClosingsDocument,
  UpdateClosingDocument,
  UpsertServiceOpeningsDocument,
} from '../../services/graphql/graphql.ts';

export const scheduleApi = {
  listServiceOpenings: (serviceId: string) =>
    gqlRequest(ListServiceOpeningsDocument, { serviceId }).then(
      (r) => r.serviceOpenings,
    ),
  upsertServiceOpenings: (serviceId: string, input: OpeningUpsertInput[]) =>
    gqlRequest(UpsertServiceOpeningsDocument, { serviceId, input }).then(
      (r) => r.upsertServiceOpenings,
    ),

  searchClosings: (venueId: string, input?: ClosingSearchInput) =>
    gqlRequest(SearchClosingsDocument, { id: venueId, input }).then(
      (r) => r.venueClosings,
    ),
  /** Every closing matching the filter, paged to completion — for the month view. */
  searchAllClosings: (venueId: string, input?: ClosingSearchInput) =>
    collectAllPages((page, pageSize) =>
      scheduleApi.searchClosings(venueId, {
        ...input,
        pagination: { page, pageSize },
      }),
    ),

  createClosing: (venueId: string, input: ClosingCreateInput) =>
    gqlRequest(CreateClosingDocument, { id: venueId, input }).then(
      (r) => r.createClosing,
    ),
  updateClosing: (venueId: string, closingId: string, input: ClosingUpdateInput) =>
    gqlRequest(UpdateClosingDocument, { id: venueId, closingId, input }).then(
      (r) => r.updateClosing,
    ),
  deleteClosing: (venueId: string, closingId: string) =>
    gqlRequest(DeleteClosingDocument, { id: venueId, closingId }).then(
      (r) => r.deleteClosing,
    ),
};

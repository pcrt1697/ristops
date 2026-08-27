import { collectAllPages } from '../../commons/utils.ts';
import { gqlRequest } from '../../services/graphql/client.ts';
import {
  type CapacityOverrideCreateInput,
  type CapacityOverrideUpdateInput,
  type ConflictCheckInput,
  type ServiceClosingCreateInput,
  type ServiceClosingUpdateInput,
  CapacityOverrideConflictsDocument,
  CreateCapacityOverrideDocument,
  CreateServiceClosingDocument,
  CreateOpeningOverrideDocument,
  DeleteCapacityOverrideDocument,
  DeleteServiceClosingDocument,
  DeleteOpeningOverrideDocument,
  ListServiceOpeningsDocument,
  type OpeningConflictCheckInput,
  type OpeningOverrideCreateInput,
  type OpeningOverrideUpdateInput,
  OpeningOverrideConflictsDocument,
  type OpeningUpsertInput,
  ServiceOpeningConflictsDocument,
  type PaginationInput,
  type ScheduleDateFilter,
  SearchCapacityOverridesDocument,
  SearchServiceClosingsDocument,
  SearchOpeningOverridesDocument,
  SearchVenueClosingsDocument,
  ServiceClosingConflictsDocument,
  UpdateCapacityOverrideDocument,
  UpdateServiceClosingDocument,
  UpdateOpeningOverrideDocument,
  UpsertServiceOpeningsDocument,
  type VenueClosingCreateInput,
  type VenueClosingUpdateInput,
  CreateVenueClosingDocument,
  DeleteVenueClosingDocument,
  UpdateVenueClosingDocument,
  VenueClosingConflictsDocument,
} from '../../services/graphql/graphql.ts';

export const scheduleApi = {
  listServiceOpenings: (serviceId: string, includeDeleted?: boolean) =>
    gqlRequest(ListServiceOpeningsDocument, { serviceId, includeDeleted }),
  upsertServiceOpenings: (serviceId: string, openings: OpeningUpsertInput[]) =>
    gqlRequest(UpsertServiceOpeningsDocument, { serviceId, openings }),
  serviceOpeningConflicts: (
    serviceId: string,
    input: OpeningConflictCheckInput,
  ) =>
    gqlRequest(ServiceOpeningConflictsDocument, { serviceId, input }).then(
      (res) => res.serviceOpeningConflicts,
    ),

  searchOpeningOverrides: (
    serviceId: string,
    filter: ScheduleDateFilter,
    pagination?: PaginationInput,
  ) =>
    gqlRequest(SearchOpeningOverridesDocument, {
      serviceId,
      input: { filter, pagination },
    }),
  searchAllOpeningOverrides: (serviceId: string, filter: ScheduleDateFilter) =>
    collectAllPages(async (page, pageSize) => {
      const res = await gqlRequest(SearchOpeningOverridesDocument, {
        serviceId,
        input: { filter, pagination: { page, pageSize } },
      });
      return res.serviceOpeningOverrides;
    }),
  createOpeningOverride: (serviceId: string, input: OpeningOverrideCreateInput) =>
    gqlRequest(CreateOpeningOverrideDocument, { serviceId, input }),
  updateOpeningOverride: (
    serviceId: string,
    overrideId: string,
    input: OpeningOverrideUpdateInput,
  ) =>
    gqlRequest(UpdateOpeningOverrideDocument, { serviceId, overrideId, input }),
  deleteOpeningOverride: (serviceId: string, overrideId: string) =>
    gqlRequest(DeleteOpeningOverrideDocument, { serviceId, overrideId }),
  openingOverrideConflicts: (serviceId: string, input: ConflictCheckInput) =>
    gqlRequest(OpeningOverrideConflictsDocument, { serviceId, input }).then(
      (res) => res.serviceOpeningOverrideConflicts,
    ),

  searchServiceClosings: (
    serviceId: string,
    filter: ScheduleDateFilter,
    pagination?: PaginationInput,
  ) =>
    gqlRequest(SearchServiceClosingsDocument, {
      serviceId,
      input: { filter, pagination },
    }),
  searchAllServiceClosings: (serviceId: string, filter: ScheduleDateFilter) =>
    collectAllPages(async (page, pageSize) => {
      const res = await gqlRequest(SearchServiceClosingsDocument, {
        serviceId,
        input: { filter, pagination: { page, pageSize } },
      });
      return res.serviceClosings;
    }),
  createServiceClosing: (serviceId: string, input: ServiceClosingCreateInput) =>
    gqlRequest(CreateServiceClosingDocument, { serviceId, input }),
  updateServiceClosing: (
    serviceId: string,
    closingId: string,
    input: ServiceClosingUpdateInput,
  ) => gqlRequest(UpdateServiceClosingDocument, { serviceId, closingId, input }),
  deleteServiceClosing: (serviceId: string, closingId: string) =>
    gqlRequest(DeleteServiceClosingDocument, { serviceId, closingId }),
  serviceClosingConflicts: (serviceId: string, input: ConflictCheckInput) =>
    gqlRequest(ServiceClosingConflictsDocument, { serviceId, input }).then(
      (res) => res.serviceClosingConflicts,
    ),

  searchCapacityOverrides: (
    serviceId: string,
    filter: ScheduleDateFilter,
    pagination?: PaginationInput,
  ) =>
    gqlRequest(SearchCapacityOverridesDocument, {
      serviceId,
      input: { filter, pagination },
    }),
  searchAllCapacityOverrides: (serviceId: string, filter: ScheduleDateFilter) =>
    collectAllPages(async (page, pageSize) => {
      const res = await gqlRequest(SearchCapacityOverridesDocument, {
        serviceId,
        input: { filter, pagination: { page, pageSize } },
      });
      return res.serviceCapacityOverrides;
    }),
  createCapacityOverride: (
    serviceId: string,
    input: CapacityOverrideCreateInput,
  ) => gqlRequest(CreateCapacityOverrideDocument, { serviceId, input }),
  updateCapacityOverride: (
    serviceId: string,
    capacityOverrideId: string,
    input: CapacityOverrideUpdateInput,
  ) =>
    gqlRequest(UpdateCapacityOverrideDocument, {
      serviceId,
      capacityOverrideId,
      input,
    }),
  deleteCapacityOverride: (serviceId: string, capacityOverrideId: string) =>
    gqlRequest(DeleteCapacityOverrideDocument, {
      serviceId,
      capacityOverrideId,
    }),
  capacityOverrideConflicts: (serviceId: string, input: ConflictCheckInput) =>
    gqlRequest(CapacityOverrideConflictsDocument, { serviceId, input }).then(
      (res) => res.serviceCapacityOverrideConflicts,
    ),

  searchVenueClosings: (
    venueId: string,
    filter: ScheduleDateFilter,
    pagination?: PaginationInput,
  ) =>
    gqlRequest(SearchVenueClosingsDocument, {
      venueId,
      input: { filter, pagination },
    }),
  searchAllVenueClosings: (venueId: string, filter: ScheduleDateFilter) =>
    collectAllPages(async (page, pageSize) => {
      const res = await gqlRequest(SearchVenueClosingsDocument, {
        venueId,
        input: { filter, pagination: { page, pageSize } },
      });
      return res.venueClosings;
    }),
  createVenueClosing: (venueId: string, input: VenueClosingCreateInput) =>
    gqlRequest(CreateVenueClosingDocument, { venueId, input }),
  updateVenueClosing: (
    venueId: string,
    closingId: string,
    input: VenueClosingUpdateInput,
  ) => gqlRequest(UpdateVenueClosingDocument, { venueId, closingId, input }),
  deleteVenueClosing: (venueId: string, closingId: string) =>
    gqlRequest(DeleteVenueClosingDocument, { venueId, closingId }),
  venueClosingConflicts: (venueId: string, input: ConflictCheckInput) =>
    gqlRequest(VenueClosingConflictsDocument, { venueId, input }).then(
      (res) => res.venueClosingConflicts,
    ),
};

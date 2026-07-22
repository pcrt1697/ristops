import { gqlRequest } from '../../services/graphql/client.ts';
import {
  CreateServiceDocument,
  type CreateServiceInput,
  DeleteServiceDocument,
  GetServiceDocument,
  ListServicesDocument,
  UpdateServiceDocument,
  type UpdateServiceInput,
} from '../../services/graphql/graphql.ts';

export const serviceApi = {
  getService: (id: string) => gqlRequest(GetServiceDocument, { id }),
  listServices: (venueId: string, name?: string, includeDeleted?: boolean) =>
    gqlRequest(ListServicesDocument, { venueId, name, includeDeleted }),
  createService: (input: CreateServiceInput) =>
    gqlRequest(CreateServiceDocument, { input }),
  updateService: (id: string, input: UpdateServiceInput) =>
    gqlRequest(UpdateServiceDocument, { id, input }),
  deleteService: (id: string) => gqlRequest(DeleteServiceDocument, { id }),
};

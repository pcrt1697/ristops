import { ClientError, GraphQLClient } from 'graphql-request';
import { RISTOPS_BFF_URL, type ServiceError } from '../common.ts';
import type { TypedDocumentNode } from '@graphql-typed-document-node/core';

const client = new GraphQLClient(`${RISTOPS_BFF_URL}/api/graphql`, {
  credentials: 'include',
  responseMiddleware: (response) => {
    if (response instanceof ClientError) {
      const gqlError = response.response.errors?.[0];
      const error = new Error(
        gqlError?.message ?? 'GraphQL error',
      ) as ServiceError;
      error.status =
        (gqlError?.extensions?.['code'] as number) ??
        response.response.status ??
        500;
      error.traceId =
        (gqlError?.extensions?.['traceId'] as string) ?? undefined;
      throw error;
    }
  },
});

export async function gqlRequest<TData, TVariables extends object>(
  document: TypedDocumentNode<TData, TVariables>,
  variables?: TVariables,
): Promise<TData> {
  return (client.request as (doc: unknown, vars?: unknown) => Promise<TData>)(
    document,
    variables,
  );
}

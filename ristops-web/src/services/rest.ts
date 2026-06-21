import { RISTOPS_BFF_URL, type ServiceError } from './common.ts';

export async function restClient<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T | ServiceError> {
  const response = await fetch(`${RISTOPS_BFF_URL}/api${endpoint}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const error = new Error(`HTTP error: ${response.status}`) as Error & {
      status: number;
      traceId?: string;
    };
    error.status = response.status;
    error.traceId = response.headers.get('x-trace-id') ?? undefined;
    throw error;
  }
  if (
    response.status === 204 ||
    response.headers.get('content-length') === '0'
  ) {
    return undefined as T;
  }
  return (await response.json()) as Promise<T>;
}

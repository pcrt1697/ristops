export const RISTOPS_BFF_URL = import.meta.env.VITE_RISTOPS_BFF_URL as string;

export interface ServiceError extends Error {
    status: number;
    traceId?: string;
}

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import type { ServiceError } from '../../services/common.ts';
import { useGlobalError } from '../../context/error.hooks.ts';

export default function GlobalQueryErrorHandler() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setError } = useGlobalError();

  useEffect(() => {
    return queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'updated' && event.query.state.status === 'error') {
        const error = event.query.state.error as ServiceError;
        if (error.status === 401) {
          void navigate('/login');
        } else {
          setError(
            error.traceId
              ? `Something went wrong. Trace ID: ${error.traceId}`
              : 'Something went wrong, please try again.',
          );
        }
      }
    });
  }, [navigate, queryClient, setError]);

  return null;
}

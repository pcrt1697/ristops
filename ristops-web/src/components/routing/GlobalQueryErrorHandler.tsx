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
        } else if (error.status !== 404) {
          // 404s mean "not found" and are handled by the caller (e.g. clearing a
          // stale selection); they aren't unexpected failures worth a global toast.
          setError(
            error.requestId
              ? `Something went wrong. Request ID: ${error.requestId}`
              : 'Something went wrong, please try again.',
          );
        }
      }
    });
  }, [navigate, queryClient, setError]);

  return null;
}

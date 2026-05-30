import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import type { ServiceError } from '../../services/common.ts';

export default function GlobalQueryErrorHandler() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    return queryClient.getQueryCache().subscribe((event) => {
      if (event.type === 'updated' && event.query.state.status === 'error') {
        console.log(event);
        const error = event.query.state.error as ServiceError;
        if (error.status === 401) {
          void navigate('/login');
        } else {
          // todo: make this prettier
          void message.error(
            error.traceId
              ? `Something went wrong. Trace ID: ${error.traceId}`
              : 'Something went wrong, please try again.',
          );
        }
      }
    });
  }, [navigate, queryClient]);

  return null;
}

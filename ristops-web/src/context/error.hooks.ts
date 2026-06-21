import { use } from 'react';
import { GlobalErrorContext, type GlobalErrorContextValue } from './error.context.ts';

export function useGlobalError(): GlobalErrorContextValue {
  const ctx = use(GlobalErrorContext);
  if (!ctx)
    throw new Error('useGlobalError must be used within GlobalErrorProvider');
  return ctx;
}

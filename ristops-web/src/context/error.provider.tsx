import { useState, type ReactNode } from 'react';
import { GlobalErrorContext } from './error.context.ts';

export function GlobalErrorProvider({ children }: { children: ReactNode }) {
  const [error, setError] = useState<string | null>(null);

  return (
    <GlobalErrorContext value={{ error, setError }}>
      {children}
    </GlobalErrorContext>
  );
}

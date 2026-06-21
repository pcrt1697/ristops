import { createContext } from 'react';

export interface GlobalErrorContextValue {
  error: string | null;
  setError: (msg: string | null) => void;
}

export const GlobalErrorContext = createContext<GlobalErrorContextValue | null>(null);

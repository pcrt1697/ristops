import { type ReactNode, useCallback, useState } from 'react';
import { VenueContext } from './venue.context.ts';

const STORAGE_KEY = 'ristops.currentVenueId';

export function CurrentVenueProvider({ children }: { children: ReactNode }) {
  const [currentVenueId, setId] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  );

  const setCurrentVenueId = useCallback((id: string | null) => {
    setId(id);
    if (id) localStorage.setItem(STORAGE_KEY, id);
    else localStorage.removeItem(STORAGE_KEY);
  }, []);

  return (
    <VenueContext value={{ currentVenueId, setCurrentVenueId }}>
      {children}
    </VenueContext>
  );
}

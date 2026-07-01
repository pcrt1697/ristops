import { createContext } from 'react';

export interface CurrentVenueContextValue {
  currentVenueId: string | null;
  setCurrentVenueId: (id: string | null) => void;
}

export const VenueContext = createContext<CurrentVenueContextValue | null>(
  null,
);

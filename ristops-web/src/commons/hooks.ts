import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * Returns a debounced copy of `value` that only updates after it has stayed
 * unchanged for `delay` ms. Useful to avoid firing a query on every keystroke.
 */
export function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/**
 * Binds a single URL query-string parameter to a `[value, setValue]` pair.
 * Writing an empty value removes the param; updates use the functional form so
 * multiple params can be edited independently without clobbering each other.
 */
export function useSearchParamState(
  key: string,
): [string, (value: string) => void] {
  const [searchParams, setSearchParams] = useSearchParams();
  const value = searchParams.get(key) ?? '';
  // Stable identity, so callers can depend on it from an effect without re-running every render.
  const setValue = useCallback(
    (next: string) =>
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          if (next) params.set(key, next);
          else params.delete(key);
          return params;
        },
        { replace: true },
      ),
    [key, setSearchParams],
  );
  return [value, setValue];
}

export interface SearchParamFilters {
  /** Reads a filter param, defaulting to an empty string when absent. */
  get: (key: string) => string;
  /** Sets/removes a filter param and resets pagination to the first page. */
  setFilter: (key: string) => (value: string) => void;
  /** Current zero-based page (0 when absent). */
  page: number;
  /** Sets the zero-based page, dropping the param for page 0. */
  setPage: (next: number) => void;
}

/**
 * Binds a paginated, filterable list's state to the URL query string. Filter
 * changes reset pagination; page changes preserve the filters. Shared by the
 * resource-grant tables (venue staff, app access) which manage identical state.
 */
export function useSearchParamFilters(): SearchParamFilters {
  const [searchParams, setSearchParams] = useSearchParams();

  const get = (key: string) => searchParams.get(key) ?? '';

  const setFilter = (key: string) => (value: string) =>
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (value) next.set(key, value);
        else next.delete(key);
        next.delete('page');
        return next;
      },
      { replace: true },
    );

  const setPage = (next: number) =>
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev);
        if (next > 0) params.set('page', String(next));
        else params.delete('page');
        return params;
      },
      { replace: true },
    );

  return { get, setFilter, page: Number(searchParams.get('page')) || 0, setPage };
}

import { useEffect, useState } from 'react';
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
  const setValue = (next: string) =>
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev);
        if (next) params.set(key, next);
        else params.delete(key);
        return params;
      },
      { replace: true },
    );
  return [value, setValue];
}

/**
 * useDebounce Hook
 * Custom hook untuk debounce value
 */

import { useState, useEffect } from 'react';

/**
 * Custom hook untuk debounce value
 * @param value - Value yang akan di-debounce
 * @param delay - Delay dalam milliseconds
 * @returns Debounced value
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;


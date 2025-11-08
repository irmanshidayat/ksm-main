/**
 * Query String Builder Utility
 */

export function buildQueryString(params: any): string {
  if (!params) return '';

  const searchParams = new URLSearchParams();

  Object.entries(params as Record<string, any>).forEach(([key, value]) => {
    if (value === undefined || value === null) return;

    if (Array.isArray(value)) {
      value.forEach((v) => {
        if (v !== undefined && v !== null) {
          searchParams.append(key, String(v));
        }
      });
      return;
    }

    // Handle boolean and numbers consistently
    searchParams.append(key, String(value));
  });

  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}


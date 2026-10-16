/**
 * useActedDateFormatter — formats an acted-on ISO timestamp as
 * "dd-mm-yyyy hh:mm" for approval sign-off displays (mirrors the stage
 * approval date, with the time added). Returns a stable formatter function.
 */

import { useCallback } from 'react';

export const useActedDateFormatter = (): ((iso: string | null) => string) =>
  useCallback((iso: string | null): string => {
    if (!iso) return '';
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return '';
    const dd = String(dt.getDate()).padStart(2, '0');
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const yyyy = dt.getFullYear();
    const hh = String(dt.getHours()).padStart(2, '0');
    const min = String(dt.getMinutes()).padStart(2, '0');
    return `${dd}-${mm}-${yyyy} ${hh}:${min}`;
  }, []);

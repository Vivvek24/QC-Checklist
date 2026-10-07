/**
 * useDashboardData — the dashboard page's "controller".
 *
 * Owns: the selected date range, the fetched payload, loading state, the
 * free-text search, the username→employee-name resolver, the summary counts,
 * and the search-filtered pending/approved row lists.
 *
 * DashboardPage stays composition + JSX only.
 */

import { useEffect, useMemo, useState } from 'react';
import { useUsers } from '../../user-management/hooks/useUsers';
import { dashboardApi } from '../api/dashboardApi';
import {
  computeRange,
  type DashboardResponse,
  type DashboardRow,
  type RangeKey,
} from '../models/DashboardTypes';

/** Pull the human-readable message out of an API error (message or detail). */
const apiErrorMessage = (e: unknown): string | undefined => {
  const data = (e as { response?: { data?: { message?: string; detail?: string } } })?.response?.data;
  return data?.message ?? data?.detail;
};

export interface UseDashboardDataOptions {
  /** Initial preset range. Defaults to 'this_month'. */
  initialRange?: RangeKey;
  /** Called with a message when a fetch fails (page shows a toast). */
  onError?: (message: string) => void;
}

export interface DashboardCounts {
  pending: number;
  approved: number;
  total: number;
}

export interface UseDashboardDataResult {
  range: RangeKey;
  setRange: (key: RangeKey) => void;
  loading: boolean;
  data: DashboardResponse | null;
  search: string;
  setSearch: (q: string) => void;
  counts: DashboardCounts;
  pendingRows: DashboardRow[];
  approvedRows: DashboardRow[];
  /** Resolve a requested_by username / employee id to the employee's name. */
  resolveName: (username: string) => string;
}

export function useDashboardData(options: UseDashboardDataOptions = {}): UseDashboardDataResult {
  const { initialRange = 'this_month', onError } = options;

  const [range, setRange] = useState<RangeKey>(initialRange);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [search, setSearch] = useState('');

  // Resolve requested_by (a username / employee id) to the employee's name.
  const { data: usersData } = useUsers(0, 500);
  const resolveName = useMemo(() => {
    const map = new Map<string, string>();
    for (const u of usersData?.users ?? []) {
      if (u.employee_name) map.set(u.username, u.employee_name);
    }
    return (username: string) => map.get(username) ?? username;
  }, [usersData]);

  // Fetch on mount and whenever the selected range changes.
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      const { from, to } = computeRange(range);
      setLoading(true);
      try {
        const res = await dashboardApi.getDashboard(from, to);
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) onError?.(apiErrorMessage(e) ?? 'Failed to load dashboard');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    run();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  const counts = useMemo<DashboardCounts>(() => ({
    pending: data?.pending.length ?? 0,
    approved: data?.approved.length ?? 0,
    total: data?.total ?? 0,
  }), [data]);

  /** Apply the free-text search to a list of rows. */
  const filterRows = (rows: DashboardRow[]): DashboardRow[] => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) =>
      [r.request_number, r.batch_no, r.product_name, r.test_name, r.format_name]
        .some((v) => (v || '').toLowerCase().includes(q))
    );
  };

  const pendingRows = useMemo(() => filterRows(data?.pending ?? []), [data, search]); // eslint-disable-line react-hooks/exhaustive-deps
  const approvedRows = useMemo(() => filterRows(data?.approved ?? []), [data, search]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    range, setRange, loading, data, search, setSearch,
    counts, pendingRows, approvedRows, resolveName,
  };
}

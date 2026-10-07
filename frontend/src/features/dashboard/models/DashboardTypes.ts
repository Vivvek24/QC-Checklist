/**
 * Dashboard domain types + presentation helpers.
 *
 * - DashboardRow / DashboardResponse mirror the GET /qc-checklist/dashboard
 *   payload.
 * - RangeKey + computeRange + RANGE_OPTIONS drive the preset date-range filter.
 * - ChipTone + STATUS_COLORS + deriveStatus turn a row's status into display
 *   text + color.
 */

export interface DashboardRow {
  request_number: string;
  format_name: string;
  status_format: string;
  created_date: string | null;
  stage_status: string;
  requested_by: string;
  request_status: string;
  is_last_stage: boolean;
  batch_no: string;
  product_name: string;
  test_name: string;
  action_flag: boolean;
}

export interface DashboardResponse {
  pending: DashboardRow[];
  approved: DashboardRow[];
  total: number;
}

/** Format a Date as a LOCAL `YYYY-MM-DD` string — not toISOString(), which
 * converts to UTC first and would shift the date back a day for +hh:mm
 * timezones. */
export function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Preset date ranges for the dashboard filter. Each computes a [from, to)
 * window (to is exclusive). */
export type RangeKey =
  | 'today' | 'yesterday' | 'last7' | 'last30'
  | 'this_month' | 'last_month' | 'this_year' | 'last_year';

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

export function computeRange(key: RangeKey): { from: Date; to: Date } {
  const now = new Date();
  const today = startOfDay(now);
  const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1);

  switch (key) {
    case 'today':
      return { from: today, to: tomorrow };
    case 'yesterday': {
      const y = new Date(today); y.setDate(today.getDate() - 1);
      return { from: y, to: today };
    }
    case 'last7': {
      const f = new Date(today); f.setDate(today.getDate() - 6);
      return { from: f, to: tomorrow };
    }
    case 'last30': {
      const f = new Date(today); f.setDate(today.getDate() - 29);
      return { from: f, to: tomorrow };
    }
    case 'this_month':
      return { from: new Date(now.getFullYear(), now.getMonth(), 1), to: new Date(now.getFullYear(), now.getMonth() + 1, 1) };
    case 'last_month':
      return { from: new Date(now.getFullYear(), now.getMonth() - 1, 1), to: new Date(now.getFullYear(), now.getMonth(), 1) };
    case 'this_year':
      return { from: new Date(now.getFullYear(), 0, 1), to: new Date(now.getFullYear() + 1, 0, 1) };
    case 'last_year':
      return { from: new Date(now.getFullYear() - 1, 0, 1), to: new Date(now.getFullYear(), 0, 1) };
  }
}

export const RANGE_OPTIONS: { label: string; value: RangeKey }[] = [
  { label: 'Today', value: 'today' },
  { label: 'Yesterday', value: 'yesterday' },
  { label: 'Last 7 Days', value: 'last7' },
  { label: 'Last 30 Days', value: 'last30' },
  { label: 'This Month', value: 'this_month' },
  { label: 'Last Month', value: 'last_month' },
  { label: 'This Year', value: 'this_year' },
  { label: 'Last Year', value: 'last_year' },
];

export type ChipTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

/** Status is shown as plain colored text (no badge). */
export const STATUS_COLORS: Record<ChipTone, string> = {
  success: '#16a34a',
  warning: '#b45309',
  danger: '#dc2626',
  info: '#2563eb',
  neutral: '#64748b',
};

/** Decompose a request's active state into { stage, label, tone }. */
export function deriveStatus(row: DashboardRow): { stage: string; label: string; tone: ChipTone } {
  const sf = (row.status_format || '').trim();
  if (sf) {
    const parts = sf.split(' - ');
    const stage = (parts[0] ?? '').trim();
    const state = parts.slice(1).join(' - ').trim();
    if (state.toLowerCase().includes('refer')) return { stage, label: 'Referred Back', tone: 'danger' };
    if (state.toLowerCase().includes('pending')) return { stage, label: 'Pending Approval', tone: 'warning' };
    return { stage, label: state || row.request_status, tone: 'info' };
  }
  const map: Record<string, { label: string; tone: ChipTone }> = {
    Approved: { label: 'Approved', tone: 'success' },
    ReferBack: { label: 'Referred Back', tone: 'danger' },
    Pending: { label: 'Pending', tone: 'warning' },
    Draft: { label: 'Draft', tone: 'neutral' },
  };
  const m = map[row.request_status] ?? { label: row.request_status, tone: 'neutral' as ChipTone };
  return { stage: '', label: m.label, tone: m.tone };
}

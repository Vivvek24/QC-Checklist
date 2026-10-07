/**
 * DashboardKpiCards — the summary cards at the top of the QC Checklist
 * dashboard. The Pending and Approved cards double as the view selector;
 * Total is informational. Styling comes from the `.kcard*` classes in
 * theme-overrides.css.
 *
 * NOTE: the card classes are named `kcard*`, NOT `kpi*`. The global rule
 * `[class*="pi-"] { font-family: 'primeicons' !important }` matches any class
 * containing the "pi-" substring (which "kpi-card" does) and would force the
 * icon font onto the card text — making it render as serif-like glyphs.
 */

export type KpiStatus = 'PENDING' | 'APPROVED' | 'TOTAL';

interface DashboardKpiCardsProps {
  pending: number;
  approved: number;
  total: number;
  loading?: boolean;
  /** The currently selected view ('PENDING' | 'APPROVED'). */
  selectedStatus?: KpiStatus;
  onStatusClick: (status: KpiStatus) => void;
}

const cards: { label: string; status: KpiStatus; icon: string; colorClass: string; selectable: boolean }[] = [
  { label: 'Pending', status: 'PENDING', icon: 'pi pi-chart-pie', colorClass: 'kcard-icon-pending', selectable: true },
  { label: 'Approved', status: 'APPROVED', icon: 'pi pi-shield', colorClass: 'kcard-icon-approved', selectable: true },
  { label: 'Total', status: 'TOTAL', icon: 'pi pi-inbox', colorClass: 'kcard-icon-total', selectable: false },
];

export const DashboardKpiCards = ({
  pending, approved, total, loading, selectedStatus, onStatusClick,
}: DashboardKpiCardsProps) => {
  const counts: Record<KpiStatus, number> = {
    PENDING: pending,
    APPROVED: approved,
    TOTAL: total,
  };

  return (
    <div className="flex gap-3 mb-4 flex-wrap mt-3">
      {cards.map((card) => (
        <div
          key={card.status}
          className={`flex-1 kcard${selectedStatus === card.status ? ' kcard-active' : ''}`}
          style={card.selectable ? undefined : { cursor: 'default' }}
          onClick={card.selectable ? () => onStatusClick(card.status) : undefined}
        >
          <div className={`kcard-icon ${card.colorClass}`}>
            <i className={card.icon} />
          </div>
          <div className="kcard-left">
            <span className="kcard-label">{card.label}</span>
          </div>
          <span className="kcard-count">{loading ? '—' : counts[card.status]}</span>
        </div>
      ))}
    </div>
  );
};

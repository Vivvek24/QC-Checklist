/**
 * Dashboard Page — pending & approved checklist requests with summary cards,
 * a preset date-range filter, status text and an action-focused table.
 *
 * This page is composition + JSX only: data loading, range/search state, the
 * name resolver and counts all live in useDashboardData; domain types + the
 * range/status helpers live in models/DashboardTypes.
 */

import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { DashboardKpiCards, type KpiStatus } from '../components/DashboardKpiCards';
import { useDashboardData } from '../hooks/useDashboardData';
import {
  RANGE_OPTIONS,
  STATUS_COLORS,
  deriveStatus,
  type ChipTone,
  type DashboardRow,
} from '../models/DashboardTypes';

const StatusText = ({ label, tone }: { label: string; tone: ChipTone }) => (
  <span style={{ color: STATUS_COLORS[tone], fontWeight: 600, fontSize: '0.76rem', whiteSpace: 'nowrap' }}>
    {label}
  </span>
);

export const DashboardPage = () => {
  const toast = useRef<Toast>(null);
  const navigate = useNavigate();

  const {
    range, setRange, loading, data, search, setSearch,
    counts, pendingRows, approvedRows, resolveName,
  } = useDashboardData({
    onError: (message) =>
      toast.current?.show({ severity: 'error', summary: 'Error', detail: message, life: 5000 }),
  });

  // The Pending / Approved summary cards double as the view selector.
  const [activeView, setActiveView] = useState<'pending' | 'approved'>('pending');

  const dateBodyTemplate = (row: DashboardRow) => {
    if (!row.created_date) return <span style={{ color: '#94a3b8' }}>—</span>;
    const d = new Date(row.created_date);
    return <span style={{ color: '#475569' }}>{d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</span>;
  };

  const requestNoBody = (row: DashboardRow) => (
    <span style={{ fontWeight: 600, color: '#1e293b' }}>{row.request_number}</span>
  );

  const stageStatusBody = (row: DashboardRow) => {
    const { stage, label, tone } = deriveStatus(row);
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
        {stage && <span style={{ fontWeight: 600, fontSize: '0.76rem', color: '#334155' }}>{stage}</span>}
        <StatusText label={label} tone={tone} />
      </div>
    );
  };

  const requestStatusBody = (row: DashboardRow) => {
    const map: Record<string, ChipTone> = {
      Approved: 'success', ReferBack: 'danger', Pending: 'warning', Draft: 'neutral',
    };
    const labelMap: Record<string, string> = { ReferBack: 'Referred Back' };
    return <StatusText label={labelMap[row.request_status] ?? row.request_status} tone={map[row.request_status] ?? 'neutral'} />;
  };

  const requestedByBody = (row: DashboardRow) => (
    <span style={{ color: '#475569' }}>{resolveName(row.requested_by) || '—'}</span>
  );

  const actionBodyTemplate = (row: DashboardRow) => (
    <div className="flex align-items-center gap-1">
      {row.action_flag && (
        <Button icon="pi pi-file-plus" rounded text raised severity="success" size="small"
          tooltip="Fill Next Stage" tooltipOptions={{ position: 'top' }}
          onClick={() => navigate(`/qc-checklist/create-request?request=${encodeURIComponent(row.request_number)}`)} />
      )}
      <Button icon="pi pi-trash" rounded text raised severity="danger" size="small"
        tooltip="Delete" tooltipOptions={{ position: 'top' }} />
    </div>
  );

  const renderTable = (rows: DashboardRow[], withActions: boolean, emptyMsg: string) => (
    <DataTable value={rows} size="small" stripedRows paginator rows={15} removableSort
      emptyMessage={emptyMsg} style={{ fontSize: '0.78rem' }}
      scrollable scrollHeight="calc(100vh - 420px)">
      <Column field="request_number" header="Request No" body={requestNoBody}
        style={{ minWidth: '9.5rem' }} className="qc-frozen-col" sortable frozen />
      {withActions && (
        <Column header="Actions" body={actionBodyTemplate}
          style={{ minWidth: '6rem', left: '9.5rem' }} className="qc-frozen-col" frozen />
      )}
      <Column field="batch_no" header="Batch No" style={{ minWidth: '9rem' }} sortable />
      <Column field="product_name" header="Product" style={{ minWidth: '12rem' }} sortable />
      <Column field="test_name" header="Test Name" style={{ minWidth: '10rem' }} sortable />
      <Column field="stage_status" header="Stage Status" body={stageStatusBody} style={{ minWidth: '13rem' }} sortable />
      <Column field="request_status" header="Request" body={requestStatusBody} style={{ minWidth: '9rem' }} sortable />
      <Column field="requested_by" header="Requested By" body={requestedByBody} style={{ minWidth: '11rem' }} sortable />
      <Column field="format_name" header="Format" style={{ minWidth: '13rem' }} sortable />
      <Column header="Date" body={dateBodyTemplate} field="created_date" style={{ minWidth: '9rem' }} sortable />
    </DataTable>
  );

  return (
    <div className="qc-dashboard" style={{ padding: '1rem 1.25rem' }}>
      <Toast ref={toast} />

      {/* ─── Header ─── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 700, color: '#1e293b' }}>QC Checklist Dashboard</h2>
          <p style={{ margin: '0.2rem 0 0', fontSize: '0.8rem', color: '#64748b' }}>
            Track and act on checklist requests across their lifecycle.
          </p>
        </div>
        <div className="flex flex-column gap-1">
          <label style={{ fontSize: '0.72rem', fontWeight: 600, color: '#64748b' }}>Date Range</label>
          <Dropdown
            value={range}
            options={RANGE_OPTIONS}
            onChange={(e) => setRange(e.value)}
            style={{ width: '220px' }}
          />
        </div>
      </div>

      {/* ─── Summary cards (also the view selector) ─── */}
      <DashboardKpiCards
        pending={counts.pending}
        approved={counts.approved}
        total={counts.total}
        loading={loading}
        selectedStatus={activeView === 'pending' ? 'PENDING' : 'APPROVED'}
        onStatusClick={(s: KpiStatus) => {
          if (s === 'PENDING') setActiveView('pending');
          else if (s === 'APPROVED') setActiveView('approved');
        }}
      />

      {/* ─── Content ─── */}
      {loading && !data && (
        <div className="flex align-items-center justify-content-center py-6">
          <ProgressSpinner style={{ width: '40px', height: '40px' }} strokeWidth="3" />
        </div>
      )}

      {data && (
        <div style={{ background: '#fff', border: '1px solid #e9ecef', borderRadius: '12px', padding: '0.9rem 1rem 1rem', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <i className={`pi ${activeView === 'pending' ? 'pi pi-chart-pie' : 'pi pi-shield'}`}
                style={{ color: activeView === 'pending' ? '#f59e0b' : '#16a34a' }} />
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>
                {activeView === 'pending' ? 'Pending Requests' : 'Approved Requests'}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
              <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
                <i className="pi pi-search" style={{
                  position: 'absolute', left: '0.65rem', top: '50%', transform: 'translateY(-50%)',
                  color: '#94a3b8', fontSize: '0.8rem', pointerEvents: 'none',
                }} />
                <InputText
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search.."
                  style={{ width: '320px', fontSize: '0.8rem', paddingLeft: '2rem' }}
                />
              </span>
            </div>
          </div>
          {activeView === 'pending'
            ? renderTable(pendingRows, true, 'No matching pending requests.')
            : renderTable(approvedRows, false, 'No matching approved requests.')}
        </div>
      )}
    </div>
  );
};

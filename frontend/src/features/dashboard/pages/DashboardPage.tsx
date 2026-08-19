/**
 * Dashboard Page — shows pending and approved checklist requests in two tabs.
 * Filters: from_date, to_date (default: current month).
 */

import { useRef, useState, useEffect } from 'react';
import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { TabView, TabPanel } from 'primereact/tabview';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { apiClient } from '@shared/services/apiClient';

interface DashboardRow {
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

interface DashboardResponse {
  pending: DashboardRow[];
  approved: DashboardRow[];
}

function getMonthRange(): { from: Date; to: Date } {
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), 1);
  const to = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return { from, to };
}

function formatDate(d: Date): string {
  return d.toISOString().split('T')[0]!;
}

export const DashboardPage = () => {
  const toast = useRef<Toast>(null);
  const { from: defaultFrom, to: defaultTo } = getMonthRange();

  const [fromDate, setFromDate] = useState<Date>(defaultFrom);
  const [toDate, setToDate] = useState<Date>(defaultTo);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DashboardResponse | null>(null);

  const fetchData = async (from: Date, to: Date) => {
    setLoading(true);
    try {
      const { data: res } = await apiClient.get<DashboardResponse>('/qc-checklist/dashboard', {
        params: { from_date: formatDate(from), to_date: formatDate(to) },
      });
      setData(res);
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed to load dashboard', life: 5000 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(fromDate, toDate);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = () => {
    fetchData(fromDate, toDate);
  };

  const dateBodyTemplate = (row: DashboardRow) => {
    if (!row.created_date) return '-';
    const d = new Date(row.created_date);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const actionBodyTemplate = (row: DashboardRow) => (
    <div className="flex align-items-center gap-1">
      {row.action_flag && (
        <Button icon="pi pi-arrow-right" rounded text raised severity="success" size="small"
          tooltip="Fill Next Stage" tooltipOptions={{ position: 'top' }} />
      )}
      <Button icon="pi pi-trash" rounded text raised severity="danger" size="small"
        tooltip="Delete" tooltipOptions={{ position: 'top' }} />
    </div>
  );

  const columns = [
    { field: 'request_number', header: 'Request No', style: { width: '9rem' } },
    { field: 'batch_no', header: 'Batch No', style: { width: '8rem' } },
    { field: 'product_name', header: 'Product', style: { minWidth: '10rem' } },
    { field: 'test_name', header: 'Test Name', style: { minWidth: '8rem' } },
    { field: 'stage_status', header: 'Stage Status', style: { width: '7rem' } },
    { field: 'request_status', header: 'Request Status', style: { width: '7rem' } },
    { field: 'requested_by', header: 'Requested By', style: { width: '8rem' } },
    { field: 'format_name', header: 'Format', style: { minWidth: '12rem' } },
  ];

  return (
    <div className="p-3">
      <Toast ref={toast} />

      <h2 className="text-xl font-semibold text-900 mt-0 mb-3">Dashboard</h2>

      {/* Filters */}
      <div className="flex align-items-end gap-3 mb-3">
        <div className="flex flex-column gap-1">
          <label className="font-medium text-sm">From Date</label>
          <Calendar value={fromDate} onChange={(e) => setFromDate(e.value as Date)}
            dateFormat="dd M yy" showIcon style={{ width: '180px' }} />
        </div>
        <div className="flex flex-column gap-1">
          <label className="font-medium text-sm">To Date</label>
          <Calendar value={toDate} onChange={(e) => setToDate(e.value as Date)}
            dateFormat="dd M yy" showIcon style={{ width: '180px' }} />
        </div>
        <Button label="Search" icon="pi pi-search" size="small" onClick={handleSearch} loading={loading} />
      </div>

      {/* Content */}
      {loading && !data && (
        <div className="flex align-items-center justify-content-center py-5">
          <ProgressSpinner style={{ width: '40px', height: '40px' }} strokeWidth="3" />
        </div>
      )}

      {data && (
        <TabView>
          <TabPanel header={`Pending (${data.pending.length})`}>
            <DataTable value={data.pending} size="small" stripedRows paginator rows={20}
              emptyMessage="No pending requests" style={{ fontSize: '0.78rem' }}
              scrollable scrollHeight="calc(100vh - 320px)">
              <Column field="request_number" header="Request No" style={{ width: '9rem' }} sortable />
              <Column header="Actions" body={actionBodyTemplate} style={{ width: '6rem' }} />
              {columns.filter(c => c.field !== 'request_number').map((col) => (
                <Column key={col.field} field={col.field} header={col.header} style={col.style}
                  sortable />
              ))}
              <Column header="Date" body={dateBodyTemplate} style={{ width: '7rem' }} sortable
                field="created_date" />
            </DataTable>
          </TabPanel>
          <TabPanel header={`Approved (${data.approved.length})`}>
            <DataTable value={data.approved} size="small" stripedRows paginator rows={20}
              emptyMessage="No approved requests" style={{ fontSize: '0.78rem' }}
              scrollable scrollHeight="calc(100vh - 320px)">
              {columns.map((col) => (
                <Column key={col.field} field={col.field} header={col.header} style={col.style}
                  sortable />
              ))}
              <Column header="Date" body={dateBodyTemplate} style={{ width: '7rem' }} sortable
                field="created_date" />
            </DataTable>
          </TabPanel>
        </TabView>
      )}
    </div>
  );
};

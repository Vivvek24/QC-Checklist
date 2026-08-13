/**
 * Formats View page — shows all formats with "View Stages" and "View All Questions" links.
 * This is the main entry page for format-stage-question configuration.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { DataTable, type DataTableFilterMeta } from 'primereact/datatable';
import { useFormats } from '../hooks/useFormats';
import type { Format } from '../models/Format';

const defaultFilters: DataTableFilterMeta = {
  format_no: { value: null, matchMode: FilterMatchMode.CONTAINS },
  format_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

export const FormatsViewPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);
  const { data, isLoading, refetch, isRefetching } = useFormats();
  const navigate = useNavigate();

  return (
    <div className="p-3">
      <div className="mb-3">
        <h2 className="text-xl font-semibold text-900 m-0">Formats View</h2>
        <p className="text-600 mt-1 mb-0">View formats and manage stage-question mappings</p>
      </div>

      <div className="surface-card p-3 border-round shadow-1">
        <div className="flex gap-2 mb-3">
          <Button label="Refresh" icon="pi pi-refresh" severity="secondary" outlined
            loading={isRefetching} onClick={() => refetch()} type="button" />
        </div>

        <DataTable
          value={data?.items ?? []}
          loading={isLoading || isRefetching}
          paginator rows={10} rowsPerPageOptions={[10, 25, 50, 100]}
          stripedRows
          filters={filters} filterDisplay="row"
          onFilter={(e) => setFilters(e.filters)}
          emptyMessage="No formats found."
        >
          <Column field="format_no" header="Format No" sortable filter filterPlaceholder="Search..." />
          <Column field="format_name" header="Format Name" sortable filter filterPlaceholder="Search..." />
          <Column header="Stage" body={(row: Format) => (
            <span className="cursor-pointer font-medium" style={{ color: 'var(--color-primary)', fontSize: '0.8rem' }}
              onClick={() => navigate(`/masters/formats-view/${row.id}/stages`)}>View Stages</span>
          )} />
          <Column header="Question" body={(row: Format) => (
            <span className="cursor-pointer font-medium" style={{ color: 'var(--color-primary)', fontSize: '0.8rem' }}
              onClick={() => navigate(`/masters/formats-view/${row.id}/questions`)}>View All Questions</span>
          )} />
        </DataTable>
      </div>
    </div>
  );
};

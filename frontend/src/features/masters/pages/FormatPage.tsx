/**
 * Format master screen.
 */

import { useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import { Tag } from 'primereact/tag';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { FormatForm } from '../components/FormatForm';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useFormats, useCreateFormat, useUpdateFormat, useDeleteFormat } from '../hooks/useFormats';
import { useUnits } from '../hooks/useUnits';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { Format, CreateFormatRequest } from '../models/Format';

const defaultFilters: DataTableFilterMeta = {
  format_no: { value: null, matchMode: FilterMatchMode.CONTAINS },
  format_title: { value: null, matchMode: FilterMatchMode.CONTAINS },
  format_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

const FORMAT_TYPE_SEVERITY: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
  Chromatographic: 'info',
  AQL: 'success',
  RECEIPT_CHECKLIST_STANDARD: 'warning',
  ReconcilationSheet: 'danger',
};

export const FormatPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);

  const { data, isLoading, refetch, isRefetching } = useFormats();
  const createMutation = useCreateFormat();
  const updateMutation = useUpdateFormat();
  const deleteMutation = useDeleteFormat();

  const { data: unitData } = useUnits();
  const unitMap = Object.fromEntries((unitData?.items ?? []).map((u) => [u.id, u.name]));

  const permissions = useMasterPermissions('formats');

  const crud = useMasterCrudController<Format, CreateFormatRequest>({
    entityLabel: 'Format',
    labelOf: (row) => row.format_no,
    onCreate: (request) => createMutation.mutateAsync(request),
    onUpdate: (id, request) => updateMutation.mutateAsync({ id, request }),
    onDelete: (id) => deleteMutation.mutateAsync(id),
  });

  return (
    <MasterCrudPage<Format>
      title="Formats"
      subtitle="Manage format master data"
      newLabel="New Format"
      rows={data?.items ?? []}
      loading={isLoading || isRefetching}
      refreshing={isRefetching}
      onRefresh={() => refetch()}
      onNew={crud.openCreate}
      canCreate={permissions.canCreate}
      filters={filters}
      onFilterChange={setFilters}
      emptyMessage="No formats defined yet."
      toastRef={crud.toast}
      columns={
        <>
          <Column field="format_no" header="Format No" sortable filter filterPlaceholder="Search..." style={{ width: '9rem' }} />
          <Column field="format_title" header="Title" sortable filter filterPlaceholder="Search..." />
          <Column field="format_name" header="Name" sortable filter filterPlaceholder="Search..." />
          <Column header="Unit" body={(row: Format) => unitMap[row.unit_id] ?? '—'} style={{ width: '9rem' }} />
          <Column
            header="Type"
            body={(row: Format) => (
              <Tag value={row.format_type} severity={FORMAT_TYPE_SEVERITY[row.format_type] ?? 'info'} />
            )}
            style={{ width: '12rem' }}
          />
          <Column
            header="Decl. Q"
            body={(row: Format) => <Tag value={row.has_declaration_question ? 'Yes' : 'No'} severity={row.has_declaration_question ? 'success' : 'danger'} />}
            style={{ width: '6rem' }}
          />
          <Column
            header="Status"
            body={(row: Format) => <MasterStatusTag isActive={row.is_active} />}
            style={{ width: '7rem' }}
          />
          {permissions.canModifyRows && (
            <Column
              header="Actions"
              body={(row: Format) => (
                <MasterRowActions
                  label={row.format_no}
                  canUpdate={permissions.canUpdate}
                  canDelete={permissions.canDelete}
                  onEdit={() => crud.openEdit(row)}
                  onDelete={() => crud.requestDelete(row)}
                />
              )}
              style={{ width: '7rem' }}
            />
          )}
        </>
      }
    >
      <FormatForm
        visible={crud.dialogVisible}
        format={crud.editing}
        saving={createMutation.isPending || updateMutation.isPending}
        onHide={crud.closeDialog}
        onSubmit={crud.submit}
      />
    </MasterCrudPage>
  );
};

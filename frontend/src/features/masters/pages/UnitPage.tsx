/**
 * Unit master screen.
 */

import { useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { UnitForm } from '../components/UnitForm';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useUnits, useCreateUnit, useUpdateUnit, useDeleteUnit } from '../hooks/useUnits';
import { useBusinessUnits } from '../hooks/useBusinessUnits';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { Unit, CreateUnitRequest } from '../models/Unit';

const defaultFilters: DataTableFilterMeta = {
  name: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

export const UnitPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);

  const { data, isLoading, refetch, isRefetching } = useUnits();
  const createMutation = useCreateUnit();
  const updateMutation = useUpdateUnit();
  const deleteMutation = useDeleteUnit();

  // Build a lookup map for business unit names
  const { data: buData } = useBusinessUnits();
  const buMap = Object.fromEntries((buData?.items ?? []).map((bu) => [bu.id, bu.name]));

  const permissions = useMasterPermissions('units');

  const crud = useMasterCrudController<Unit, CreateUnitRequest>({
    entityLabel: 'Unit',
    labelOf: (row) => row.name,
    onCreate: (request) => createMutation.mutateAsync(request),
    onUpdate: (id, request) => updateMutation.mutateAsync({ id, request }),
    onDelete: (id) => deleteMutation.mutateAsync(id),
  });

  return (
    <MasterCrudPage<Unit>
      title="Units"
      subtitle="Manage unit master data"
      newLabel="New Unit"
      rows={data?.items ?? []}
      loading={isLoading || isRefetching}
      refreshing={isRefetching}
      onRefresh={() => refetch()}
      onNew={crud.openCreate}
      canCreate={permissions.canCreate}
      filters={filters}
      onFilterChange={setFilters}
      emptyMessage="No units defined yet."
      toastRef={crud.toast}
      columns={
        <>
          <Column field="name" header="Name" sortable filter filterPlaceholder="Search..." />
          <Column
            header="Business Unit"
            body={(row: Unit) => buMap[row.business_unit_id] ?? '—'}
            sortable
            field="business_unit_id"
          />
          <Column
            header="Status"
            body={(row: Unit) => <MasterStatusTag isActive={row.is_active} />}
            style={{ width: '8rem' }}
          />
          {permissions.canModifyRows && (
            <Column
              header="Actions"
              body={(row: Unit) => (
                <MasterRowActions
                  label={row.name}
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
      <UnitForm
        visible={crud.dialogVisible}
        unit={crud.editing}
        saving={createMutation.isPending || updateMutation.isPending}
        onHide={crud.closeDialog}
        onSubmit={crud.submit}
      />
    </MasterCrudPage>
  );
};

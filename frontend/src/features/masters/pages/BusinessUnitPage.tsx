/**
 * Business Unit master screen.
 */

import { useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { BusinessUnitForm } from '../components/BusinessUnitForm';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import {
  useBusinessUnits,
  useCreateBusinessUnit,
  useDeleteBusinessUnit,
  useUpdateBusinessUnit,
} from '../hooks/useBusinessUnits';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { BusinessUnit, CreateBusinessUnitRequest } from '../models/BusinessUnit';

const defaultFilters: DataTableFilterMeta = {
  name: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

export const BusinessUnitPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);

  const { data, isLoading, refetch, isRefetching } = useBusinessUnits();
  const createMutation = useCreateBusinessUnit();
  const updateMutation = useUpdateBusinessUnit();
  const deleteMutation = useDeleteBusinessUnit();

  const permissions = useMasterPermissions('business_units');

  const crud = useMasterCrudController<BusinessUnit, CreateBusinessUnitRequest>({
    entityLabel: 'Business Unit',
    labelOf: (row) => row.name,
    onCreate: (request) => createMutation.mutateAsync(request),
    onUpdate: (id, request) => updateMutation.mutateAsync({ id, request }),
    onDelete: (id) => deleteMutation.mutateAsync(id),
  });

  return (
    <MasterCrudPage<BusinessUnit>
      title="Business Units"
      subtitle="Manage business unit master data"
      newLabel="New Business Unit"
      rows={data?.items ?? []}
      loading={isLoading || isRefetching}
      refreshing={isRefetching}
      onRefresh={() => refetch()}
      onNew={crud.openCreate}
      canCreate={permissions.canCreate}
      filters={filters}
      onFilterChange={setFilters}
      emptyMessage="No business units defined yet."
      toastRef={crud.toast}
      columns={
        <>
          <Column
            field="name"
            header="Name"
            sortable
            filter
            filterPlaceholder="Search..."
          />
          <Column
            header="Status"
            body={(row: BusinessUnit) => <MasterStatusTag isActive={row.is_active} />}
            style={{ width: '8rem' }}
          />
          {permissions.canModifyRows && (
            <Column
              header="Actions"
              body={(row: BusinessUnit) => (
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
      <BusinessUnitForm
        visible={crud.dialogVisible}
        businessUnit={crud.editing}
        saving={createMutation.isPending || updateMutation.isPending}
        onHide={crud.closeDialog}
        onSubmit={crud.submit}
      />
    </MasterCrudPage>
  );
};

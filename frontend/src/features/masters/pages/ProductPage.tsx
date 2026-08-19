import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FilterMatchMode } from 'primereact/api';
import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { ProductForm } from '../components/ProductForm';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useProducts, useCreateProduct, useUpdateProduct, useDeleteProduct } from '../hooks/useProducts';
import { useMasterCrudController } from '../hooks/useMasterCrudController';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import type { Product, CreateProductRequest } from '../models/Product';

const defaultFilters: DataTableFilterMeta = {
  product_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

export const ProductPage = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);
  const { data, isLoading, refetch, isRefetching } = useProducts();
  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();
  const permissions = useMasterPermissions('products');

  const crud = useMasterCrudController<Product, CreateProductRequest>({
    entityLabel: 'Product', labelOf: (row) => row.product_name,
    onCreate: (r) => createMutation.mutateAsync(r),
    onUpdate: (id, r) => updateMutation.mutateAsync({ id, request: r }),
    onDelete: (id) => deleteMutation.mutateAsync(id),
  });

  return (
    <MasterCrudPage<Product>
      title="Products" subtitle="Manage product master data" newLabel="New Product"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching}
      onRefresh={() => refetch()} onNew={crud.openCreate} canCreate={permissions.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No products defined yet." toastRef={crud.toast}
      columns={
        <>
          <Column field="product_name" header="Product Name" sortable filter filterPlaceholder="Search..." />
          <Column field="storage_conditions" header="Storage Conditions" body={(row: Product) => row.storage_conditions || '—'} />
          <Column header="Tests" body={(row: Product) => (
            <Button label="Tests" icon="pi pi-link" rounded text raised size="small" severity="success"
              onClick={() => navigate(`/masters/products/${row.id}/tests`)} type="button" />
          )} style={{ width: '8rem' }} />
          <Column header="Status" body={(row: Product) => <MasterStatusTag isActive={row.is_active} />} style={{ width: '8rem' }} />
          {permissions.canModifyRows && (
            <Column header="Actions" body={(row: Product) => (
              <MasterRowActions label={row.product_name} canUpdate={permissions.canUpdate} canDelete={permissions.canDelete}
                onEdit={() => crud.openEdit(row)} onDelete={() => crud.requestDelete(row)} />
            )} style={{ width: '7rem' }} />
          )}
        </>
      }
    >
      <ProductForm visible={crud.dialogVisible} product={crud.editing}
        saving={createMutation.isPending || updateMutation.isPending}
        onHide={crud.closeDialog} onSubmit={crud.submit} />
    </MasterCrudPage>
  );
};

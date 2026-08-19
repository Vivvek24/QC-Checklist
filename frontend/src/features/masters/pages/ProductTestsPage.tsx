/**
 * Product Tests Page — shows tests associated with a specific product.
 * Route: /masters/products/:productId/tests
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { Toast } from 'primereact/toast';
import { apiClient } from '@shared/services/apiClient';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { TestMasterForm } from '../components/TestMasterForm';
import type { TestMaster, CreateTestMasterRequest } from '../models/TestMaster';

export const ProductTestsPage = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const toast = useRef<Toast>(null);

  const [tests, setTests] = useState<TestMaster[]>([]);
  const [loading, setLoading] = useState(true);
  const [productName, setProductName] = useState('');
  const [dialogVisible, setDialogVisible] = useState(false);
  const [editing, setEditing] = useState<TestMaster | null>(null);
  const [saving, setSaving] = useState(false);

  const loadTests = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{ items: TestMaster[] }>(
        '/masters/test-masters', { params: { product_id: productId } }
      );
      setTests(data.items ?? []);
    } catch {
      setTests([]);
    } finally {
      setLoading(false);
    }
  }, [productId]);

  const loadProductName = useCallback(async () => {
    try {
      const { data } = await apiClient.get<{ product_name: string }>(`/masters/products/${productId}`);
      setProductName(data.product_name);
    } catch {
      setProductName('');
    }
  }, [productId]);

  useEffect(() => { loadTests(); loadProductName(); }, [loadTests, loadProductName]);

  const handleSubmit = async (formData: CreateTestMasterRequest) => {
    setSaving(true);
    try {
      if (editing) {
        await apiClient.patch(`/masters/test-masters/${editing.id}`, formData);
        toast.current?.show({ severity: 'success', summary: 'Updated', detail: 'Test updated successfully.', life: 3000 });
      } else {
        await apiClient.post('/masters/test-masters', formData);
        toast.current?.show({ severity: 'success', summary: 'Created', detail: 'Test created successfully.', life: 3000 });
      }
      setDialogVisible(false);
      setEditing(null);
      loadTests();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (test: TestMaster) => {
    try {
      await apiClient.delete(`/masters/test-masters/${test.id}`);
      toast.current?.show({ severity: 'success', summary: 'Deleted', detail: `Test '${test.test_name}' deleted.`, life: 3000 });
      loadTests();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Failed', life: 5000 });
    }
  };

  return (
    <div className="p-3">
      <Toast ref={toast} />
      <div className="flex align-items-center gap-2 mb-3">
        <Button icon="pi pi-arrow-left" severity="secondary" text
          onClick={() => navigate('/masters/products')} type="button" />
        <div>
          <h2 className="text-xl font-semibold text-900 m-0">{productName || 'Loading...'}</h2>
          <p className="text-600 mt-1 mb-0">Tests associated with this product</p>
        </div>
      </div>

      <div className="surface-card p-3 border-round shadow-1">
        <div className="flex gap-2 mb-3">
          <Button label="Add Test" icon="pi pi-plus" size="small" type="button"
            onClick={() => { setEditing(null); setDialogVisible(true); }} />
          <Button label="Refresh" icon="pi pi-refresh" severity="secondary" outlined size="small"
            loading={loading} onClick={() => loadTests()} type="button" />
        </div>

        <DataTable value={tests} loading={loading} size="small" stripedRows paginator rows={10}
          emptyMessage="No tests for this product yet.">
          <Column field="test_name" header="Test Name" sortable />
          <Column field="sample_description" header="Sample Description" />
          <Column field="sample_qty" header="Sample Qty" style={{ width: '8rem' }} />
          <Column header="Status" body={(row: TestMaster) => <MasterStatusTag isActive={row.is_active} />} style={{ width: '7rem' }} />
          <Column header="Actions" body={(row: TestMaster) => (
            <MasterRowActions label={row.test_name} canUpdate={true} canDelete={true}
              onEdit={() => { setEditing(row); setDialogVisible(true); }}
              onDelete={() => handleDelete(row)} />
          )} style={{ width: '7rem' }} />
        </DataTable>
      </div>

      <TestMasterForm
        visible={dialogVisible}
        test={editing}
        productId={Number(productId)}
        saving={saving}
        onHide={() => { setDialogVisible(false); setEditing(null); }}
        onSubmit={handleSubmit}
      />
    </div>
  );
};

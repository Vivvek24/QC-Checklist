/**
 * LDAP Servers management page (Management section).
 * Grid of configured LDAP servers with add / edit / delete.
 */

import { useRef, useState } from 'react';

import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { Tag } from 'primereact/tag';
import { Toast } from 'primereact/toast';

import { extractApiError } from '@shared/utils/apiError';

import type { LdapConfig, LdapConfigCreateRequest } from '../api/ldapApi';
import { LdapConfigDialog } from '../components/LdapConfigDialog';
import { useLdapConfigs, useCreateLdapConfig, useUpdateLdapConfig } from '../hooks/useLdap';

export const LdapServersPage = () => {
  const toast = useRef<Toast>(null);

  const { data, isLoading } = useLdapConfigs();
  const createMutation = useCreateLdapConfig();
  const updateMutation = useUpdateLdapConfig();

  const [dialogVisible, setDialogVisible] = useState(false);
  const [editing, setEditing] = useState<LdapConfig | null>(null);

  const showError = (error: unknown, fallback: string) => {
    toast.current?.show({
      severity: 'error',
      summary: 'Error',
      detail: extractApiError(error, fallback),
      life: 5000,
    });
  };

  const openCreate = () => {
    setEditing(null);
    setDialogVisible(true);
  };

  const openEdit = (config: LdapConfig) => {
    setEditing(config);
    setDialogVisible(true);
  };

  const handleSubmit = async (form: LdapConfigCreateRequest) => {
    if (!form.name.trim() || !form.server_uri.trim() || !form.bind_username.trim()) {
      toast.current?.show({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Name, Server URI and Bind Username are required',
        life: 3000,
      });
      return;
    }
    try {
      if (editing) {
        await updateMutation.mutateAsync({
          id: editing.id,
          request: {
            ...form,
            bind_password: form.bind_password?.trim() ? form.bind_password : null,
          },
        });
        toast.current?.show({
          severity: 'success',
          summary: 'Saved',
          detail: 'LDAP server updated',
          life: 3000,
        });
      } else {
        if (!form.bind_password.trim()) {
          toast.current?.show({
            severity: 'warn',
            summary: 'Validation',
            detail: 'Bind password is required',
            life: 3000,
          });
          return;
        }
        await createMutation.mutateAsync(form);
        toast.current?.show({
          severity: 'success',
          summary: 'Created',
          detail: 'LDAP server created',
          life: 3000,
        });
      }
      setDialogVisible(false);
      setEditing(null);
    } catch (error) {
      showError(error, 'Failed to save LDAP server');
    }
  };

  const boolTemplate = (value: boolean) => (
    <Tag value={value ? 'Yes' : 'No'} severity={value ? 'success' : 'secondary'} />
  );

  const actionsTemplate = (row: LdapConfig) => (
    <div className="flex gap-1">
      <Button
        icon="pi pi-pencil"
        rounded
        outlined
        severity="info"
        size="small"
        onClick={() => openEdit(row)}
        tooltip="Edit"
        tooltipOptions={{ position: 'top' }}
        aria-label="Edit"
      />
    </div>
  );

  return (
    <div className="p-4">
      <Toast ref={toast} />

      {/* Header */}
      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">LDAP Servers</h2>
          <p className="text-600 mt-1 mb-0">Manage Active Directory / LDAP server configurations</p>
        </div>
        <Button
          label="New LDAP Server"
          icon="pi pi-plus"
          onClick={openCreate}
          aria-label="New LDAP server"
        />
      </div>

      {/* Grid */}
      <div className="surface-card p-4 border-round shadow-1">
        <DataTable
          value={data?.configs ?? []}
          loading={isLoading}
          paginator
          rows={10}
          rowsPerPageOptions={[5, 10, 25]}
          stripedRows
          showGridlines
          emptyMessage="No LDAP servers configured yet. Click 'New LDAP Server' to add one."
          aria-label="LDAP servers table"
        >
          <Column field="name" header="Name" sortable style={{ minWidth: '150px' }} />
          <Column field="server_uri" header="Server URI" style={{ minWidth: '180px' }} />
          <Column field="base_dn" header="Base DN" style={{ minWidth: '160px' }} />
          <Column field="bind_username" header="Bind Username" style={{ minWidth: '160px' }} />
          <Column field="domain_prefix" header="Domain Prefix" style={{ minWidth: '120px' }} />
          <Column
            header="SSL"
            body={(row: LdapConfig) => boolTemplate(row.use_ssl)}
            style={{ width: '5rem' }}
          />
          <Column
            header="Enabled"
            body={(row: LdapConfig) => boolTemplate(row.is_enabled)}
            style={{ width: '6rem' }}
          />
          <Column header="Actions" body={actionsTemplate} style={{ width: '8rem' }} />
        </DataTable>
      </div>

      {/* Create / Edit Dialog */}
      <LdapConfigDialog
        visible={dialogVisible}
        config={editing}
        loading={createMutation.isPending || updateMutation.isPending}
        onHide={() => {
          setDialogVisible(false);
          setEditing(null);
        }}
        onSubmit={handleSubmit}
      />
    </div>
  );
};

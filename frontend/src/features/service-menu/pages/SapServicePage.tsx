/**
 * SAP Integration Service page.
 * Checks SAP connectivity and runs the QC_Checklist lookup, showing the parsed
 * item fields plus the raw response for troubleshooting.
 */

import { useRef, useState } from 'react';
import { Button } from 'primereact/button';
import { InputText } from 'primereact/inputtext';
import { Toast } from 'primereact/toast';
import { Card } from 'primereact/card';
import { Tag } from 'primereact/tag';
import { Divider } from 'primereact/divider';
import { ProgressSpinner } from 'primereact/progressspinner';
import { useSapHealth, useSapQcChecklist } from '../hooks/useSap';

export const SapServicePage = () => {
  const toast = useRef<Toast>(null);

  const { data: healthData, isLoading: healthLoading, refetch: refetchHealth } = useSapHealth();

  const [inspLot, setInspLot] = useState('');
  const qcMutation = useSapQcChecklist();

  const statusSeverity = (status: string | undefined) => {
    if (status === 'reachable') return 'success';
    if (status === 'unreachable') return 'danger';
    return 'info';
  };

  const handleLookup = async () => {
    if (!inspLot.trim()) {
      toast.current?.show({ severity: 'warn', summary: 'Validation', detail: 'Inspection Lot (I_INSP) is required', life: 3000 });
      return;
    }
    try {
      await qcMutation.mutateAsync(inspLot.trim());
      toast.current?.show({ severity: 'success', summary: 'Success', detail: 'QC checklist fetched from SAP', life: 3000 });
    } catch (error: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: error.response?.data?.detail || 'Failed to fetch from SAP', life: 5000 });
    }
  };

  const item = qcMutation.data?.item;
  const itemRows = item ? Object.entries(item) : [];

  return (
    <div className="p-4">
      <Toast ref={toast} />

      {/* Header */}
      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">SAP Integration Service</h2>
          <p className="text-600 mt-1 mb-0">Verify SAP connectivity and look up a QC checklist by inspection lot</p>
        </div>
        <Tag
          value={healthData?.status === 'reachable' ? 'Online' : 'Offline'}
          severity={statusSeverity(healthData?.status)}
          icon={healthData?.status === 'reachable' ? 'pi pi-check-circle' : 'pi pi-times-circle'}
        />
      </div>

      {/* Service Health */}
      <Card title="Service Health" subTitle="Check connectivity to the SAP Integration Suite" className="mb-4">
        {healthLoading ? (
          <div className="flex align-items-center gap-2">
            <ProgressSpinner style={{ width: '24px', height: '24px' }} />
            <span>Checking service status...</span>
          </div>
        ) : (
          <div className="grid">
            <div className="col-12 md:col-8">
              <div className="flex flex-column gap-2">
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '120px' }}>Service:</span>
                  <span>{healthData?.service || 'SAP Integration Suite'}</span>
                </div>
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '120px' }}>Status:</span>
                  <Tag value={healthData?.status || 'unknown'} severity={statusSeverity(healthData?.status)} />
                </div>
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '120px' }}>Configured:</span>
                  <Tag value={healthData?.configured ? 'Yes' : 'No'} severity={healthData?.configured ? 'success' : 'warning'} />
                </div>
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '120px' }}>Base URL:</span>
                  <span className="text-sm" style={{ wordBreak: 'break-all' }}>{healthData?.base_url || '-'}</span>
                </div>
                {healthData?.status_code && (
                  <div className="flex align-items-center gap-2">
                    <span className="font-semibold text-600" style={{ minWidth: '120px' }}>HTTP Code:</span>
                    <span>{healthData.status_code}</span>
                  </div>
                )}
                {healthData?.error && (
                  <div className="flex align-items-center gap-2">
                    <span className="font-semibold text-600" style={{ minWidth: '120px' }}>Error:</span>
                    <span className="text-red-500 text-sm">{healthData.error}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="col-12 md:col-4 flex align-items-end justify-content-end">
              <Button label="Refresh" icon="pi pi-refresh" severity="secondary" outlined onClick={() => refetchHealth()} aria-label="Refresh health" />
            </div>
          </div>
        )}
      </Card>

      <Divider />

      {/* QC Checklist lookup */}
      <Card title="GET /Get/QC_Checklist" subTitle="Look up material / batch details by inspection lot (I_INSP)" className="mb-4">
        <div className="grid">
          <div className="col-12 md:col-8">
            <label htmlFor="insp-lot" className="block font-medium mb-2">Inspection Lot (I_INSP)</label>
            <InputText id="insp-lot" value={inspLot} onChange={(e) => setInspLot(e.target.value)} placeholder="e.g. 10002237044" className="w-full" />
          </div>
          <div className="col-12 md:col-4 flex align-items-end">
            <Button label="Lookup" icon="pi pi-search" onClick={handleLookup} loading={qcMutation.isPending} />
          </div>
        </div>

        {itemRows.length > 0 && (
          <div className="mt-3 p-3 surface-100 border-round">
            <div className="flex align-items-center justify-content-between mb-2">
              <span className="font-semibold text-sm text-600">Parsed Item</span>
              <Tag value="200 OK" severity="success" />
            </div>
            <div className="grid">
              {itemRows.map(([key, value]) => (
                <div key={key} className="col-12 md:col-6 flex gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '110px' }}>{key}:</span>
                  <span className="text-sm" style={{ wordBreak: 'break-all' }}>{String(value ?? '')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {qcMutation.data && (
          <div className="mt-3 p-3 surface-100 border-round">
            <span className="font-semibold text-sm text-600">Raw Response</span>
            <pre className="text-xs overflow-auto m-0 mt-2" style={{ maxHeight: '300px' }}>
              {JSON.stringify(qcMutation.data.raw_response, null, 2)}
            </pre>
          </div>
        )}
      </Card>
    </div>
  );
};

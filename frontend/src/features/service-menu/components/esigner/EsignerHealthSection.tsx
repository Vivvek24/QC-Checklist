/**
 * E-Signer — Service Health section.
 * Shows connectivity/config details. Expanded by default.
 */

import { Button } from 'primereact/button';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tag } from 'primereact/tag';

import { useEsignerHealth } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';

const getStatusSeverity = (status: string | undefined) => {
  if (status === 'reachable') return 'success';
  if (status === 'unreachable') return 'danger';
  return 'info';
};

export const EsignerHealthSection = () => {
  const { data: healthData, isLoading, refetch } = useEsignerHealth();

  return (
    <CollapsibleSection
      title="Service Health"
      subTitle="Connectivity to the E-Signer service"
      defaultCollapsed={false}
    >
      {isLoading ? (
        <div className="flex align-items-center gap-2">
          <ProgressSpinner style={{ width: '24px', height: '24px' }} />
          <span>Checking service status...</span>
        </div>
      ) : (
        <div className="grid">
          <div className="col-12 md:col-8">
            <div className="flex flex-column gap-2">
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '120px' }}>
                  Service:
                </span>
                <span>{healthData?.service || 'E-Signer'}</span>
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '120px' }}>
                  Status:
                </span>
                <Tag
                  value={healthData?.status || 'unknown'}
                  severity={getStatusSeverity(healthData?.status)}
                />
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '120px' }}>
                  Configured:
                </span>
                <Tag
                  value={healthData?.configured ? 'Yes' : 'No'}
                  severity={healthData?.configured ? 'success' : 'warning'}
                />
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '120px' }}>
                  Base URL:
                </span>
                <span className="text-sm" style={{ wordBreak: 'break-all' }}>
                  {healthData?.base_url || '-'}
                </span>
              </div>
              {healthData?.status_code && (
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '120px' }}>
                    HTTP Code:
                  </span>
                  <span>{healthData.status_code}</span>
                </div>
              )}
              {healthData?.error && (
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '120px' }}>
                    Error:
                  </span>
                  <span className="text-red-500 text-sm">{healthData.error}</span>
                </div>
              )}
            </div>
          </div>
          <div className="col-12 md:col-4 flex align-items-end justify-content-end">
            <Button
              label="Refresh"
              icon="pi pi-refresh"
              severity="secondary"
              outlined
              onClick={() => refetch()}
              aria-label="Refresh health"
            />
          </div>
        </div>
      )}
    </CollapsibleSection>
  );
};

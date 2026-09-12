/**
 * Darwinbox — Service Health section. Expanded by default.
 */

import { Button } from 'primereact/button';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tag } from 'primereact/tag';

import { useDarwinboxHealth } from '../../hooks/useDarwinbox';
import { CollapsibleSection } from '../CollapsibleSection';

const getStatusSeverity = (status: string | undefined) => {
  if (status === 'reachable') return 'success';
  if (status === 'unreachable') return 'danger';
  return 'info';
};

export const DarwinboxHealthSection = () => {
  const { data: healthData, isLoading, refetch } = useDarwinboxHealth();

  return (
    <CollapsibleSection
      title="Service Health"
      subTitle="Connectivity to the Darwinbox master API"
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
                <span className="font-semibold text-600" style={{ minWidth: '150px' }}>
                  Service:
                </span>
                <span>{healthData?.service || 'Darwinbox (Employee Master)'}</span>
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '150px' }}>
                  Status:
                </span>
                <Tag
                  value={healthData?.status || 'unknown'}
                  severity={getStatusSeverity(healthData?.status)}
                />
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '150px' }}>
                  Active configured:
                </span>
                <Tag
                  value={healthData?.active_configured ? 'Yes' : 'No'}
                  severity={healthData?.active_configured ? 'success' : 'warning'}
                />
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '150px' }}>
                  Inactive configured:
                </span>
                <Tag
                  value={healthData?.inactive_configured ? 'Yes' : 'No'}
                  severity={healthData?.inactive_configured ? 'success' : 'warning'}
                />
              </div>
              <div className="flex align-items-center gap-2">
                <span className="font-semibold text-600" style={{ minWidth: '150px' }}>
                  Base URL:
                </span>
                <span className="text-sm" style={{ wordBreak: 'break-all' }}>
                  {healthData?.base_url || '-'}
                </span>
              </div>
              {healthData?.error && (
                <div className="flex align-items-center gap-2">
                  <span className="font-semibold text-600" style={{ minWidth: '150px' }}>
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

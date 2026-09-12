/**
 * E-Signer — GetWorkflowInfo section.
 * Fetches the status/details of a workflow by its WorkflowId.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputNumber } from 'primereact/inputnumber';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useEsignerWorkflowInfo } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EsignerWorkflowInfoSection = ({ notify }: ServiceSectionProps) => {
  const [workflowId, setWorkflowId] = useState<number | null>(null);
  const workflowInfoMutation = useEsignerWorkflowInfo();

  const handleGetWorkflowInfo = async () => {
    if (!workflowId) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter a WorkflowId.',
        life: 3000,
      });
      return;
    }
    try {
      const result = await workflowInfoMutation.mutateAsync(workflowId);
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'Workflow Info',
        detail:
          result.Messages?.filter(Boolean).join(' ') ||
          (result.IsSuccess ? 'Details found' : 'No details found'),
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to fetch workflow info'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="GET /workflow-info"
      subTitle="Logs in for an access token, then fetches the status/details of a workflow by its WorkflowId."
    >
      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="workflow-id" className="block font-medium mb-2">
            Workflow ID
          </label>
          <InputNumber
            inputId="workflow-id"
            value={workflowId}
            onValueChange={(e) => setWorkflowId(e.value ?? null)}
            useGrouping={false}
            placeholder="e.g. 174707"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Get Status"
            icon="pi pi-search"
            onClick={handleGetWorkflowInfo}
            loading={workflowInfoMutation.isPending}
          />
        </div>
      </div>
      {workflowInfoMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2 flex-wrap">
            <Tag
              value={workflowInfoMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={workflowInfoMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={workflowInfoMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {workflowInfoMutation.data.Messages?.filter(Boolean).map((m, i) => (
              <span key={i} className="text-sm text-700">
                {m}
              </span>
            ))}
          </div>
          <pre className="text-xs overflow-auto m-0" style={{ maxHeight: '300px' }}>
            {JSON.stringify(workflowInfoMutation.data, null, 2)}
          </pre>
        </div>
      )}
    </CollapsibleSection>
  );
};

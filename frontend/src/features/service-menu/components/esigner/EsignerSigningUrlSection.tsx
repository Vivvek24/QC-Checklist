/**
 * E-Signer — GetSigningURL section.
 * Fetches the ad-hoc signing URL for a workflow by its WorkFlowId.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputNumber } from 'primereact/inputnumber';
import { InputText } from 'primereact/inputtext';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useEsignerSigningUrl } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EsignerSigningUrlSection = ({ notify }: ServiceSectionProps) => {
  const [signingWorkflowId, setSigningWorkflowId] = useState<number | null>(null);
  const signingUrlMutation = useEsignerSigningUrl();

  const handleGetSigningUrl = async () => {
    if (!signingWorkflowId) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter a WorkflowId.',
        life: 3000,
      });
      return;
    }
    try {
      const result = await signingUrlMutation.mutateAsync(signingWorkflowId);
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'Signing URL',
        detail:
          result.Messages?.filter(Boolean).join(' ') ||
          (result.IsSuccess ? 'URL fetched' : 'No URL found'),
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to fetch signing URL'),
        life: 5000,
      });
    }
  };

  const url = signingUrlMutation.data?.Response ?? null;

  const copyUrl = async () => {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      notify({
        severity: 'success',
        summary: 'Copied',
        detail: 'URL copied to clipboard.',
        life: 3000,
      });
    } catch {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: 'Could not copy the URL.',
        life: 3000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="GET /signing-url"
      subTitle="Logs in for an access token, then fetches the ad-hoc signing URL for a workflow."
    >
      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="signing-workflow-id" className="block font-medium mb-2">
            Workflow ID
          </label>
          <InputNumber
            inputId="signing-workflow-id"
            value={signingWorkflowId}
            onValueChange={(e) => setSigningWorkflowId(e.value ?? null)}
            useGrouping={false}
            placeholder="e.g. 165628"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Get URL"
            icon="pi pi-link"
            onClick={handleGetSigningUrl}
            loading={signingUrlMutation.isPending}
          />
        </div>
      </div>
      {signingUrlMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-3 flex-wrap">
            <Tag
              value={signingUrlMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={signingUrlMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={signingUrlMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {signingUrlMutation.data.Messages?.filter(Boolean).map((m, i) => (
              <span key={i} className="text-sm text-700">
                {m}
              </span>
            ))}
          </div>
          {url && (
            <div className="flex align-items-center gap-2">
              <InputText value={url} readOnly className="w-full text-sm" />
              <Button
                icon="pi pi-copy"
                text
                aria-label="Copy URL"
                tooltip="Copy"
                onClick={copyUrl}
              />
              <Button
                icon="pi pi-external-link"
                text
                aria-label="Open URL"
                tooltip="Open in new tab"
                onClick={() => window.open(url, '_blank', 'noopener,noreferrer')}
              />
            </div>
          )}
        </div>
      )}
    </CollapsibleSection>
  );
};

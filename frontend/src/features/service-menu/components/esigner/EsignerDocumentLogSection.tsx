/**
 * E-Signer — GetDocumentLog section.
 * Fetches the audit-log history of a workflow's documents by its WorkflowId.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputNumber } from 'primereact/inputnumber';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import { useEsignerDocumentLog } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

export const EsignerDocumentLogSection = ({ notify }: ServiceSectionProps) => {
  const [logWorkflowId, setLogWorkflowId] = useState<number | null>(null);
  const documentLogMutation = useEsignerDocumentLog();

  const handleGetDocumentLog = async () => {
    if (!logWorkflowId) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter a WorkflowId.',
        life: 3000,
      });
      return;
    }
    try {
      const result = await documentLogMutation.mutateAsync(logWorkflowId);
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'Document Log',
        detail:
          result.Messages?.filter(Boolean).join(' ') ||
          (result.IsSuccess ? 'Document log retrieved' : 'No log found'),
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to fetch document log'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="GET /document-log"
      subTitle="Logs in for an access token, then fetches the audit-log history of a workflow's documents."
    >
      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="log-workflow-id" className="block font-medium mb-2">
            Workflow ID
          </label>
          <InputNumber
            inputId="log-workflow-id"
            value={logWorkflowId}
            onValueChange={(e) => setLogWorkflowId(e.value ?? null)}
            useGrouping={false}
            placeholder="e.g. 76808"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Get Log"
            icon="pi pi-history"
            onClick={handleGetDocumentLog}
            loading={documentLogMutation.isPending}
          />
        </div>
      </div>
      {documentLogMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-3 flex-wrap">
            <Tag
              value={documentLogMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={documentLogMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={documentLogMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {documentLogMutation.data.Messages?.filter(Boolean).map((m, i) => (
              <span key={i} className="text-sm text-700">
                {m}
              </span>
            ))}
          </div>
          {documentLogMutation.data.Response?.length ? (
            <div className="flex flex-column gap-3">
              {documentLogMutation.data.Response.map((doc, docIdx) => (
                <div key={docIdx} className="surface-0 border-round p-3">
                  <div className="flex align-items-center gap-2 mb-2">
                    <i className="pi pi-file-pdf text-red-500" />
                    <span className="font-medium text-sm">
                      {doc.DocumentName || `Document ${docIdx + 1}`}
                    </span>
                  </div>
                  {doc.DocumentLogs?.length ? (
                    <ul className="list-none p-0 m-0 flex flex-column gap-2">
                      {doc.DocumentLogs.map((entry, entryIdx) => (
                        <li
                          key={entryIdx}
                          className="flex gap-2 pb-2 border-bottom-1 surface-border"
                        >
                          <i className="pi pi-circle-fill text-primary text-xs mt-1" />
                          <div className="flex flex-column">
                            <span className="text-sm text-900">{entry.Action}</span>
                            <span className="text-xs text-600">
                              {entry.DateTime}
                              {entry.UserEmail ? ` · ${entry.UserEmail}` : ''}
                            </span>
                            <span className="text-xs text-500">
                              {entry.IPAddress ? `IP ${entry.IPAddress}` : ''}
                              {entry.OSandBrowser && entry.OSandBrowser !== 'N/A'
                                ? ` · ${entry.OSandBrowser}`
                                : ''}
                            </span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-sm text-600">No log entries.</span>
                  )}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </CollapsibleSection>
  );
};

/**
 * E-Signer — GetWorkflowAttachments section.
 * Downloads a workflow's attachments (base64) and lets the user save each file.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputNumber } from 'primereact/inputnumber';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import type { EsignerWorkflowAttachment } from '../../api/esignerApi';
import { useEsignerWorkflowAttachments } from '../../hooks/useEsigner';
import { CollapsibleSection } from '../CollapsibleSection';
import type { ServiceSectionProps } from '../sectionProps';

const fileIcon = (name: string | null): string => {
  const ext = name?.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'pdf') return 'pi pi-file-pdf text-red-500';
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'webp', 'tif', 'tiff'].includes(ext))
    return 'pi pi-image text-blue-500';
  if (['doc', 'docx'].includes(ext)) return 'pi pi-file-word text-blue-700';
  if (['xls', 'xlsx'].includes(ext)) return 'pi pi-file-excel text-green-600';
  return 'pi pi-file text-600';
};

const mimeTypeForFile = (name: string | null): string => {
  const ext = name?.split('.').pop()?.toLowerCase() ?? '';
  const map: Record<string, string> = {
    pdf: 'application/pdf',
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    gif: 'image/gif',
    svg: 'image/svg+xml',
    bmp: 'image/bmp',
    webp: 'image/webp',
    tif: 'image/tiff',
    tiff: 'image/tiff',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    txt: 'text/plain',
  };
  return map[ext] || 'application/octet-stream';
};

export const EsignerWorkflowAttachmentsSection = ({ notify }: ServiceSectionProps) => {
  const [attachmentsWorkflowId, setAttachmentsWorkflowId] = useState<number | null>(null);
  const workflowAttachmentsMutation = useEsignerWorkflowAttachments();

  const handleGetAttachments = async () => {
    if (!attachmentsWorkflowId) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter a WorkflowId.',
        life: 3000,
      });
      return;
    }
    try {
      const result = await workflowAttachmentsMutation.mutateAsync(attachmentsWorkflowId);
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'Workflow Attachments',
        detail:
          result.Messages?.filter(Boolean).join(' ') ||
          (result.IsSuccess ? 'Attachments retrieved' : 'No attachments found'),
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to fetch attachments'),
        life: 5000,
      });
    }
  };

  const saveBase64File = (attachment: EsignerWorkflowAttachment) => {
    if (!attachment.Base64FileData) return;
    try {
      const byteChars = atob(attachment.Base64FileData);
      const byteNumbers = new Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) {
        byteNumbers[i] = byteChars.charCodeAt(i);
      }
      const blob = new Blob([new Uint8Array(byteNumbers)], {
        type: mimeTypeForFile(attachment.AttachmentName),
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = attachment.AttachmentName || `attachment-${attachment.DocumentID}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: 'Could not decode the file data.',
        life: 4000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="GET /workflow-attachments"
      subTitle="Logs in for an access token, then downloads a workflow's attachments as base64 files."
    >
      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="attachments-workflow-id" className="block font-medium mb-2">
            Workflow ID
          </label>
          <InputNumber
            inputId="attachments-workflow-id"
            value={attachmentsWorkflowId}
            onValueChange={(e) => setAttachmentsWorkflowId(e.value ?? null)}
            useGrouping={false}
            placeholder="e.g. 76808"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Get Attachments"
            icon="pi pi-paperclip"
            onClick={handleGetAttachments}
            loading={workflowAttachmentsMutation.isPending}
          />
        </div>
      </div>
      {workflowAttachmentsMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2 flex-wrap">
            <Tag
              value={workflowAttachmentsMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={workflowAttachmentsMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={workflowAttachmentsMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {workflowAttachmentsMutation.data.Messages?.filter(Boolean).map((m, i) => (
              <span key={i} className="text-sm text-700">
                {m}
              </span>
            ))}
          </div>
          {workflowAttachmentsMutation.data.Response?.length ? (
            <div className="flex flex-column gap-2 mb-3">
              {workflowAttachmentsMutation.data.Response.map((attachment) => (
                <div
                  key={attachment.DocumentID}
                  className="flex align-items-center justify-content-between p-2 surface-0 border-round"
                >
                  <div className="flex align-items-center gap-2">
                    <i className={fileIcon(attachment.AttachmentName)} />
                    <div className="flex flex-column">
                      <span className="text-sm">
                        {attachment.AttachmentName || `attachment-${attachment.DocumentID}`}
                      </span>
                      <span className="text-xs text-600">
                        {attachment.NoOfPages} page(s) · {attachment.FileSize} KB
                        {attachment.UploaderName ? ` · ${attachment.UploaderName}` : ''}
                        {attachment.UploadedDate ? ` · ${attachment.UploadedDate}` : ''}
                      </span>
                    </div>
                  </div>
                  <Button
                    label="Save"
                    icon="pi pi-download"
                    size="small"
                    text
                    onClick={() => saveBase64File(attachment)}
                    disabled={!attachment.Base64FileData}
                  />
                </div>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </CollapsibleSection>
  );
};

/**
 * E-Signer — DownloadWorkflowDocuments section.
 * Downloads a workflow's documents (base64) and lets the user save each file.
 */

import { useState } from 'react';

import { Button } from 'primereact/button';
import { InputNumber } from 'primereact/inputnumber';
import { Tag } from 'primereact/tag';

import { extractApiError } from '@shared/utils/apiError';

import type { EsignerDownloadedFile } from '../../api/esignerApi';
import { useEsignerWorkflowDocuments } from '../../hooks/useEsigner';
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

export const EsignerWorkflowDocumentsSection = ({ notify }: ServiceSectionProps) => {
  const [downloadWorkflowId, setDownloadWorkflowId] = useState<number | null>(null);
  const workflowDocumentsMutation = useEsignerWorkflowDocuments();

  const handleDownloadDocuments = async () => {
    if (!downloadWorkflowId) {
      notify({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Enter a WorkflowId.',
        life: 3000,
      });
      return;
    }
    try {
      const result = await workflowDocumentsMutation.mutateAsync(downloadWorkflowId);
      notify({
        severity: result.IsSuccess ? 'success' : 'warn',
        summary: 'Download Documents',
        detail:
          result.Messages?.filter(Boolean).join(' ') ||
          (result.IsSuccess ? 'Documents downloaded' : 'No documents found'),
        life: 5000,
      });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, 'Failed to download documents'),
        life: 5000,
      });
    }
  };

  const saveBase64File = (file: EsignerDownloadedFile) => {
    if (!file.Base64FileData) return;
    try {
      const byteChars = atob(file.Base64FileData);
      const byteNumbers = new Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) {
        byteNumbers[i] = byteChars.charCodeAt(i);
      }
      const blob = new Blob([new Uint8Array(byteNumbers)], {
        type: mimeTypeForFile(file.DocumentName),
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.DocumentName || `document-${file.DocumentId}`;
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
      title="GET /workflow-documents"
      subTitle="Logs in for an access token, then downloads a workflow's documents as base64 files."
    >
      <div className="grid">
        <div className="col-12 md:col-4">
          <label htmlFor="download-workflow-id" className="block font-medium mb-2">
            Workflow ID
          </label>
          <InputNumber
            inputId="download-workflow-id"
            value={downloadWorkflowId}
            onValueChange={(e) => setDownloadWorkflowId(e.value ?? null)}
            useGrouping={false}
            placeholder="e.g. 59209"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
        <div className="col-12 md:col-4 flex align-items-end">
          <Button
            label="Download"
            icon="pi pi-download"
            onClick={handleDownloadDocuments}
            loading={workflowDocumentsMutation.isPending}
          />
        </div>
      </div>
      {workflowDocumentsMutation.data && (
        <div className="mt-3 p-3 surface-100 border-round">
          <div className="flex align-items-center gap-3 mb-2 flex-wrap">
            <Tag
              value={workflowDocumentsMutation.data.IsSuccess ? 'Success' : 'Failed'}
              severity={workflowDocumentsMutation.data.IsSuccess ? 'success' : 'danger'}
              icon={workflowDocumentsMutation.data.IsSuccess ? 'pi pi-check' : 'pi pi-times'}
            />
            {workflowDocumentsMutation.data.Messages?.filter(Boolean).map((m, i) => (
              <span key={i} className="text-sm text-700">
                {m}
              </span>
            ))}
          </div>
          {workflowDocumentsMutation.data.Response?.FileList?.length ? (
            <div className="flex flex-column gap-2 mb-3">
              {workflowDocumentsMutation.data.Response.FileList.map((file) => (
                <div
                  key={file.DocumentId}
                  className="flex align-items-center justify-content-between p-2 surface-0 border-round"
                >
                  <div className="flex align-items-center gap-2">
                    <i className={fileIcon(file.DocumentName)} />
                    <span className="text-sm">
                      {file.DocumentName || `document-${file.DocumentId}`}
                    </span>
                    {file.IsAttachment && <Tag value="Attachment" severity="info" />}
                  </div>
                  <Button
                    label="Save"
                    icon="pi pi-download"
                    size="small"
                    text
                    onClick={() => saveBase64File(file)}
                    disabled={!file.Base64FileData}
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

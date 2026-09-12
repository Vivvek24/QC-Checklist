/**
 * Published E-Signer Service page.
 *
 * A test harness for the drop-in E-Signer ("Catalyst") endpoints exposed to
 * other applications at /rest/embededsign/v1/*. Calls hit the real published
 * paths directly, sending the optional X-API-Key exactly as an external caller
 * would. Note the intentional per-endpoint query-param casing differences.
 */

import { useRef, useState } from 'react';

import { Tag } from 'primereact/tag';
import { Toast, type ToastMessage } from 'primereact/toast';

import { PublishedLoginAndSendSection } from '../components/esigner/PublishedLoginAndSendSection';
import { PublishedWorkflowNumberSection } from '../components/esigner/PublishedWorkflowNumberSection';
import { PublishedApiKeyBar } from '../components/PublishedApiKeyBar';
import {
  usePublishedGetStatus,
  usePublishedDownloadDocument,
  usePublishedGetAttachments,
  usePublishedGetDocumentLogs,
  usePublishedGetSignatureUrl,
} from '../hooks/usePublishedEsigner';

export const PublishedEsignerPage = () => {
  const toast = useRef<Toast>(null);
  const notify = (message: ToastMessage) => toast.current?.show(message);
  const [apiKey, setApiKey] = useState('');

  const getStatus = usePublishedGetStatus();
  const downloadDocument = usePublishedDownloadDocument();
  const getAttachments = usePublishedGetAttachments();
  const getDocumentLogs = usePublishedGetDocumentLogs();
  const getSignatureUrl = usePublishedGetSignatureUrl();

  return (
    <div className="p-4">
      <Toast ref={toast} />

      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">E-Signer (Published)</h2>
          <p className="text-600 mt-1 mb-0">
            Test the drop-in E-Signer endpoints exposed to other applications at
            <code className="ml-1">/rest/embededsign/v1</code>
          </p>
        </div>
        <Tag value="Published" severity="info" icon="pi pi-globe" />
      </div>

      <PublishedApiKeyBar apiKey={apiKey} onChange={setApiKey} />

      <PublishedLoginAndSendSection notify={notify} apiKey={apiKey} />

      <PublishedWorkflowNumberSection
        title="GET /Get_Status"
        subTitle="Workflow/document status (query: WorkFlowId)"
        paramLabel="WorkFlowId"
        buttonLabel="Get Status"
        buttonIcon="pi pi-info-circle"
        apiKey={apiKey}
        notify={notify}
        mutation={getStatus}
        buildVars={(key, id) => ({ apiKey: key, workFlowId: id })}
      />

      <PublishedWorkflowNumberSection
        title="POST /Download_Document"
        subTitle="Download a workflow's documents as base64 (body: WorkFlowId)"
        paramLabel="WorkFlowId"
        buttonLabel="Download"
        buttonIcon="pi pi-download"
        apiKey={apiKey}
        notify={notify}
        mutation={downloadDocument}
        buildVars={(key, id) => ({ apiKey: key, workFlowId: id })}
      />

      <PublishedWorkflowNumberSection
        title="GET /GetAttachments"
        subTitle="Workflow attachments as a bare JSON array (query: workflowId)"
        paramLabel="workflowId"
        buttonLabel="Get Attachments"
        buttonIcon="pi pi-paperclip"
        apiKey={apiKey}
        notify={notify}
        mutation={getAttachments}
        buildVars={(key, id) => ({ apiKey: key, workflowId: id })}
      />

      <PublishedWorkflowNumberSection
        title="GET /GetDocumentLogs"
        subTitle="Document audit log as a bare JSON array (query: workflowId)"
        paramLabel="workflowId"
        buttonLabel="Get Logs"
        buttonIcon="pi pi-history"
        apiKey={apiKey}
        notify={notify}
        mutation={getDocumentLogs}
        buildVars={(key, id) => ({ apiKey: key, workflowId: id })}
      />

      <PublishedWorkflowNumberSection
        title="GET /GetSignatureURL"
        subTitle="Ad-hoc signing URL envelope (query: WorkflowID)"
        paramLabel="WorkflowID"
        buttonLabel="Get URL"
        buttonIcon="pi pi-link"
        apiKey={apiKey}
        notify={notify}
        mutation={getSignatureUrl}
        buildVars={(key, id) => ({ apiKey: key, workflowId: id })}
      />
    </div>
  );
};

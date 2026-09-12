/**
 * E-Signer Service page.
 * Composes the per-endpoint section components. Each section owns its own
 * state and API calls; this page just lays them out and provides a shared
 * toast + the header status.
 */

import { useRef } from 'react';

import { Tag } from 'primereact/tag';
import { Toast, type ToastMessage } from 'primereact/toast';

import { EsignerChangePasswordSection } from '../components/esigner/EsignerChangePasswordSection';
import { EsignerDocumentLogSection } from '../components/esigner/EsignerDocumentLogSection';
import { EsignerHealthSection } from '../components/esigner/EsignerHealthSection';
import { EsignerInitiateSigningSection } from '../components/esigner/EsignerInitiateSigningSection';
import { EsignerLoginSection } from '../components/esigner/EsignerLoginSection';
import { EsignerSigningUrlSection } from '../components/esigner/EsignerSigningUrlSection';
import { EsignerWorkflowAttachmentsSection } from '../components/esigner/EsignerWorkflowAttachmentsSection';
import { EsignerWorkflowDocumentsSection } from '../components/esigner/EsignerWorkflowDocumentsSection';
import { EsignerWorkflowInfoSection } from '../components/esigner/EsignerWorkflowInfoSection';
import { useEsignerHealth } from '../hooks/useEsigner';

export const EsignerServicePage = () => {
  const toast = useRef<Toast>(null);
  const notify = (message: ToastMessage) => toast.current?.show(message);

  const { data: healthData } = useEsignerHealth();
  const online = healthData?.status === 'reachable';

  return (
    <div className="p-4">
      <Toast ref={toast} />

      {/* Header */}
      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">E-Signer Service</h2>
          <p className="text-600 mt-1 mb-0">Check connectivity to the E-Signer service</p>
        </div>
        <Tag
          value={online ? 'Online' : 'Offline'}
          severity={online ? 'success' : 'danger'}
          icon={online ? 'pi pi-check-circle' : 'pi pi-times-circle'}
        />
      </div>

      <EsignerHealthSection />
      <EsignerLoginSection notify={notify} />
      <EsignerChangePasswordSection notify={notify} />
      <EsignerInitiateSigningSection notify={notify} />
      <EsignerWorkflowInfoSection notify={notify} />
      <EsignerWorkflowDocumentsSection notify={notify} />
      <EsignerWorkflowAttachmentsSection notify={notify} />
      <EsignerDocumentLogSection notify={notify} />
      <EsignerSigningUrlSection notify={notify} />
    </div>
  );
};

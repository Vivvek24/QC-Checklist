/**
 * Published Darwin AD Service page.
 *
 * A test harness for the drop-in Darwin AD endpoints that other applications
 * consume (mounted at /adintegratorservices/rest/v1/*). Calls hit the real
 * published paths directly, sending the optional X-API-Key exactly as an
 * external caller would.
 */

import { useRef, useState } from 'react';

import { Tag } from 'primereact/tag';
import { Toast, type ToastMessage } from 'primereact/toast';

import { PublishedEmployeeDetailsSection } from '../components/darwin-ad/PublishedEmployeeDetailsSection';
import { PublishedGetEmployeesSection } from '../components/darwin-ad/PublishedGetEmployeesSection';
import { PublishedHierarchySection } from '../components/darwin-ad/PublishedHierarchySection';
import { PublishedSelectedEmployeesSection } from '../components/darwin-ad/PublishedSelectedEmployeesSection';
import { PublishedValidateCredentialsSection } from '../components/darwin-ad/PublishedValidateCredentialsSection';
import { PublishedApiKeyBar } from '../components/PublishedApiKeyBar';

export const PublishedDarwinAdPage = () => {
  const toast = useRef<Toast>(null);
  const notify = (message: ToastMessage) => toast.current?.show(message);
  const [apiKey, setApiKey] = useState('');

  return (
    <div className="p-4">
      <Toast ref={toast} />

      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">Darwin AD (Published)</h2>
          <p className="text-600 mt-1 mb-0">
            Test the drop-in Darwin AD endpoints exposed to other applications at
            <code className="ml-1">/adintegratorservices/rest/v1</code>
          </p>
        </div>
        <Tag value="Published" severity="info" icon="pi pi-globe" />
      </div>

      <PublishedApiKeyBar apiKey={apiKey} onChange={setApiKey} />

      <PublishedGetEmployeesSection notify={notify} apiKey={apiKey} />
      <PublishedSelectedEmployeesSection notify={notify} apiKey={apiKey} />
      <PublishedEmployeeDetailsSection notify={notify} apiKey={apiKey} />
      <PublishedHierarchySection notify={notify} apiKey={apiKey} />
      <PublishedValidateCredentialsSection notify={notify} apiKey={apiKey} />
    </div>
  );
};

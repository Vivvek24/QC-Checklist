/**
 * Darwinbox Service page.
 * Composes the per-endpoint section components.
 */

import { useRef } from 'react';

import { Tag } from 'primereact/tag';
import { Toast, type ToastMessage } from 'primereact/toast';

import { DarwinboxHealthSection } from '../components/darwinbox/DarwinboxHealthSection';
import { DarwinboxPreviewSection } from '../components/darwinbox/DarwinboxPreviewSection';
import { useDarwinboxHealth } from '../hooks/useDarwinbox';

export const DarwinboxServicePage = () => {
  const toast = useRef<Toast>(null);
  const notify = (message: ToastMessage) => toast.current?.show(message);

  const { data: healthData } = useDarwinboxHealth();
  const online = healthData?.status === 'reachable';

  return (
    <div className="p-4">
      <Toast ref={toast} />

      {/* Header */}
      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">Darwinbox Service</h2>
          <p className="text-600 mt-1 mb-0">
            Check connectivity and preview employee data from the Darwinbox master API
          </p>
        </div>
        <Tag
          value={online ? 'Online' : 'Offline'}
          severity={online ? 'success' : 'danger'}
          icon={online ? 'pi pi-check-circle' : 'pi pi-times-circle'}
        />
      </div>

      <DarwinboxHealthSection />
      <DarwinboxPreviewSection notify={notify} />
    </div>
  );
};

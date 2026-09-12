/**
 * Employee AD Service page.
 * Composes the per-endpoint section components.
 */

import { useRef } from 'react';

import { Tag } from 'primereact/tag';
import { Toast, type ToastMessage } from 'primereact/toast';

import { EmployeeADAllEmployeesSection } from '../components/employee-ad/EmployeeADAllEmployeesSection';
import { EmployeeADHealthSection } from '../components/employee-ad/EmployeeADHealthSection';
import { EmployeeADHierarchySection } from '../components/employee-ad/EmployeeADHierarchySection';
import { EmployeeADSelectedSection } from '../components/employee-ad/EmployeeADSelectedSection';
import { EmployeeADValidateSection } from '../components/employee-ad/EmployeeADValidateSection';
import { useEmployeeADHealth } from '../hooks/useEmployeeAD';

export const EmployeeADServicePage = () => {
  const toast = useRef<Toast>(null);
  const notify = (message: ToastMessage) => toast.current?.show(message);

  const { data: healthData } = useEmployeeADHealth();
  const online = healthData?.status === 'reachable';

  return (
    <div className="p-4">
      <Toast ref={toast} />

      {/* Header */}
      <div className="flex align-items-center justify-content-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold text-900 m-0">Employee AD Service</h2>
          <p className="text-600 mt-1 mb-0">
            Verify and test the Darwin Active Directory integration endpoints
          </p>
        </div>
        <Tag
          value={online ? 'Online' : 'Offline'}
          severity={online ? 'success' : 'danger'}
          icon={online ? 'pi pi-check-circle' : 'pi pi-times-circle'}
        />
      </div>

      <EmployeeADHealthSection />
      <EmployeeADValidateSection notify={notify} />
      <EmployeeADSelectedSection notify={notify} />
      <EmployeeADAllEmployeesSection notify={notify} />
      <EmployeeADHierarchySection notify={notify} />
    </div>
  );
};

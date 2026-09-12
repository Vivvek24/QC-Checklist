/**
 * Published Darwin AD — GET /getHierarchyData section.
 */

import { Button } from 'primereact/button';

import { CollapsibleSection } from '@features/service-menu/components/CollapsibleSection';
import { JsonResultBlock } from '@features/service-menu/components/JsonResultBlock';

import { extractApiError } from '@shared/utils/apiError';

import { usePublishedGetHierarchy } from '../../hooks/usePublishedDarwinAd';
import type { PublishedSectionProps } from '../publishedSectionProps';

export const PublishedHierarchySection = ({ notify, apiKey }: PublishedSectionProps) => {
  const mutation = usePublishedGetHierarchy();

  const handleRun = async () => {
    try {
      await mutation.mutateAsync({ apiKey });
      notify({ severity: 'success', summary: 'Success', detail: 'Hierarchy fetched', life: 3000 });
    } catch (error) {
      notify({
        severity: 'error',
        summary: 'Error',
        detail: extractApiError(error, error instanceof Error ? error.message : 'Request failed'),
        life: 5000,
      });
    }
  };

  return (
    <CollapsibleSection
      title="GET /getHierarchyData"
      subTitle="Role/designation hierarchy built by walking the manager chain"
    >
      <Button
        label="Fetch Hierarchy"
        icon="pi pi-sitemap"
        onClick={handleRun}
        loading={mutation.isPending}
      />
      <JsonResultBlock data={mutation.data} />
    </CollapsibleSection>
  );
};

/**
 * Read-only hook wrapping GET /qc-checklist/preview.
 * Returns the full format -> stages -> sections -> questions tree used as the
 * ROWS for the template's column layout. Does not write anything.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@shared/services/apiClient';
import type { ChecklistPreview } from '../models/Preview';

export const useChecklistPreview = (formatId: number | null) =>
  useQuery({
    queryKey: ['qc-checklist', 'preview', formatId],
    enabled: formatId != null,
    staleTime: 30_000,
    queryFn: async () => {
      const { data } = await apiClient.get<ChecklistPreview>('/qc-checklist/preview', {
        params: { format_id: formatId },
      });
      return data;
    },
  });

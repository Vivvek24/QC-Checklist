/**
 * useResolvedColumns — resolves which columns TemplateDrivenSnip renders for
 * one stage, and in what order.
 *
 * The caller passes this stage's own columns (from the checklist preview's
 * stage.columns — already stage-level only, section columns are separate on
 * each section). No fallback: if a stage has no Template Studio layout
 * configured, no columns are returned and the grid renders nothing (the
 * component shows a "not configured" message instead). Response is always
 * hidden for Basic Details.
 */

import { useMemo } from 'react';
import type { ColumnPreview } from '../models/ChecklistPreview';

export interface UseResolvedColumnsResult {
  orderedColumns: ColumnPreview[];
  hasOptionColumn: boolean;
  hasAnswerColumn: boolean;
  hasResponseColumn: boolean;
}

export const useResolvedColumns = (
  columns: ColumnPreview[],
  isBasicDetails: boolean
): UseResolvedColumnsResult => {
  const orderedColumns = useMemo(() => {
    return columns
      .filter((c) => c.column_type !== 'RESPONSE' || !isBasicDetails)
      .slice()
      .sort((a, b) => a.display_order - b.display_order);
  }, [columns, isBasicDetails]);

  return {
    orderedColumns,
    hasOptionColumn: orderedColumns.some((c) => c.column_type === 'OPTION'),
    hasAnswerColumn: orderedColumns.some((c) => c.column_type === 'ANSWER'),
    hasResponseColumn: orderedColumns.some((c) => c.column_type === 'RESPONSE'),
  };
};

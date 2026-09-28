/**
 * useResolvedColumns — resolves which columns TemplateDrivenSnip renders for
 * one stage, and in what order.
 *
 * Reads only this stage's own columns (section_id === null) — Template
 * Studio's listColumnsForStage returns every section's columns flattened in
 * too, since Template Studio needs that for its own load, but this
 * component only ever renders the stage-level grid.
 *
 * Falls back to a fixed default layout (Sr No, Question, Select Options,
 * Enter Answer, Response) when the stage has no Template Studio layout
 * configured yet, so the page still works before someone has designed that
 * stage's layout. Response is always hidden for Basic Details, on either
 * path.
 */

import { useMemo } from 'react';
import type { TemplateColumnResponse } from '@features/template-studio';

type FallbackColumn = Pick<TemplateColumnResponse, 'header' | 'column_type' | 'width' | 'display_order'>;

const DEFAULT_COLUMNS: FallbackColumn[] = [
  { header: 'Sr No', column_type: 'SERIAL', width: '3.5rem', display_order: 0 },
  { header: 'Questions', column_type: 'QUESTION', width: null as unknown as string, display_order: 1 },
  { header: 'Select Options', column_type: 'OPTION', width: '20rem', display_order: 2 },
  { header: 'Enter Answer', column_type: 'ANSWER', width: '14rem', display_order: 3 },
  { header: 'Response', column_type: 'RESPONSE', width: '12rem', display_order: 4 },
];

export interface UseResolvedColumnsResult {
  orderedColumns: (TemplateColumnResponse | FallbackColumn)[];
  hasOptionColumn: boolean;
  hasAnswerColumn: boolean;
  hasResponseColumn: boolean;
}

export const useResolvedColumns = (
  columns: TemplateColumnResponse[],
  isBasicDetails: boolean
): UseResolvedColumnsResult => {
  const orderedColumns = useMemo(() => {
    const stageLevelColumns = columns.filter((c) => c.section_id == null);
    return (stageLevelColumns.length > 0 ? stageLevelColumns : DEFAULT_COLUMNS)
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

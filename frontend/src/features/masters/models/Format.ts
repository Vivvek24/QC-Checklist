/**
 * Format master types.
 */

import type { MasterListParams, MasterRecord } from './common';

export type FormatType =
  | 'Chromatographic'
  | 'AQL'
  | 'RECEIPT_CHECKLIST_STANDARD'
  | 'ReconcilationSheet';

export const FORMAT_TYPE_OPTIONS: { label: string; value: FormatType }[] = [
  { label: 'Chromatographic', value: 'Chromatographic' },
  { label: 'AQL', value: 'AQL' },
  { label: 'Receipt Checklist Standard', value: 'RECEIPT_CHECKLIST_STANDARD' },
  { label: 'Reconciliation Sheet', value: 'ReconcilationSheet' },
];

export interface Format extends MasterRecord {
  format_no: string;
  format_title: string;
  format_name: string;
  unit_id: number;
  format_type: FormatType;
  has_declaration_question: boolean;
}

export interface CreateFormatRequest {
  format_no: string;
  format_title: string;
  format_name: string;
  unit_id: number;
  format_type: FormatType;
  has_declaration_question: boolean;
  is_active: boolean;
}

export type UpdateFormatRequest = Partial<CreateFormatRequest>;

export type FormatListParams = MasterListParams;

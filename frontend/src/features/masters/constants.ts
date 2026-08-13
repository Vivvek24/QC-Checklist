/**
 * Master constants used across stages and format-stage-question mapping pages.
 */

/** The constant stage name for Basic Details — auto-created on format-stage mapping */
export const BASIC_DETAILS_STAGE = 'Basic Details';

/** Format type enum values — mirrors backend FormatType enum */
export const FORMAT_TYPE = {
  CHROMATOGRAPHIC: 'Chromatographic',
  AQL: 'AQL',
  RECEIPT_CHECKLIST_STANDARD: 'RECEIPT_CHECKLIST_STANDARD',
  RECONCILATION_SHEET: 'ReconcilationSheet',
} as const;

/** Custom answer enum values — mirrors backend CustomAnswer enum */
export const CUSTOM_ANSWER = {
  START_DATE: 'StartDate',
  END_DATE: 'EndDate',
  CALCULATE_SAMPLE_DESTROYED: 'Calculate_SampleDestroyed',
  CALCULATE_SAMPLE_CONSUMED: 'Calculate_SampleConsumed',
} as const;

export const CUSTOM_ANSWER_OPTIONS = [
  { label: 'Start Date', value: CUSTOM_ANSWER.START_DATE },
  { label: 'End Date', value: CUSTOM_ANSWER.END_DATE },
  { label: 'Calculate Sample Destroyed', value: CUSTOM_ANSWER.CALCULATE_SAMPLE_DESTROYED },
  { label: 'Calculate Sample Consumed', value: CUSTOM_ANSWER.CALCULATE_SAMPLE_CONSUMED },
];

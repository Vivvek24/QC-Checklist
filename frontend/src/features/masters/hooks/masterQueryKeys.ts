/**
 * TanStack Query keys for master data.
 *
 * Collected in one module so that a master can declare which sibling caches its
 * edits invalidate without importing that sibling's hooks — which would create
 * import cycles between, say, countries and states.
 */

import type { QueryKey } from '@tanstack/react-query';

export const MASTER_KEYS = {
  countries: ['masters', 'countries'] as QueryKey,
  states: ['masters', 'states'] as QueryKey,
  categoriesOfLaw: ['masters', 'categories-of-law'] as QueryKey,
  legislations: ['masters', 'legislations'] as QueryKey,
  rules: ['masters', 'rules'] as QueryKey,
  taskTypes: ['masters', 'task-types'] as QueryKey,
  businessUnits: ['masters', 'business-units'] as QueryKey,
  units: ['masters', 'units'] as QueryKey,
  formats: ['masters', 'formats'] as QueryKey,
  stages: ['masters', 'stages'] as QueryKey,
  questions: ['masters', 'questions'] as QueryKey,
  products: ['masters', 'products'] as QueryKey,
  validationTypes: ['masters', 'validation-types'] as QueryKey,
  remarks: ['masters', 'remarks'] as QueryKey,
  sapFields: ['masters', 'sap-fields'] as QueryKey,
  approvalLabels: ['masters', 'approval-labels'] as QueryKey,
  testMasters: ['masters', 'test-masters'] as QueryKey,
} as const;

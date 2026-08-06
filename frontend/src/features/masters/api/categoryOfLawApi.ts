/**
 * Category of law master API calls.
 * Maps to backend: /api/v1/masters/categories-of-law
 *
 * Note the path is hyphenated while the response envelope key is underscored
 * (`categories_of_law`) — both are the backend's, not a typo.
 */

import { createMasterApi } from './createMasterApi';
import type {
  CategoryOfLaw,
  CategoryOfLawListParams,
  CreateCategoryOfLawRequest,
  UpdateCategoryOfLawRequest,
} from '../models/CategoryOfLaw';

export const categoryOfLawApi = createMasterApi<
  CategoryOfLaw,
  CreateCategoryOfLawRequest,
  UpdateCategoryOfLawRequest,
  CategoryOfLawListParams
>('/masters/categories-of-law', 'categories_of_law');

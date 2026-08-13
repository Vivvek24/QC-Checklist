import { createMasterApi } from './createMasterApi';
import type { ValidationType, ValidationTypeListParams, CreateValidationTypeRequest, UpdateValidationTypeRequest } from '../models/ValidationType';
export const validationTypeApi = createMasterApi<ValidationType, CreateValidationTypeRequest, UpdateValidationTypeRequest, ValidationTypeListParams>('/masters/validation-types', 'items');

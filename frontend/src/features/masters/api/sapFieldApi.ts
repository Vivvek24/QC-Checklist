import { createMasterApi } from './createMasterApi';
import type { SapField, SapFieldListParams, CreateSapFieldRequest, UpdateSapFieldRequest } from '../models/SapField';
export const sapFieldApi = createMasterApi<SapField, CreateSapFieldRequest, UpdateSapFieldRequest, SapFieldListParams>('/masters/sap-fields', 'items');

import { createMasterApi } from './createMasterApi';
import type { TestMaster, TestMasterListParams, CreateTestMasterRequest, UpdateTestMasterRequest } from '../models/TestMaster';

export const testMasterApi = createMasterApi<TestMaster, CreateTestMasterRequest, UpdateTestMasterRequest, TestMasterListParams>(
  '/masters/test-masters', 'items'
);

import { testMasterApi } from '../api/testMasterApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { TestMaster, TestMasterListParams, CreateTestMasterRequest, UpdateTestMasterRequest } from '../models/TestMaster';

const hooks = createMasterHooks<TestMaster, CreateTestMasterRequest, UpdateTestMasterRequest, TestMasterListParams>(
  testMasterApi, MASTER_KEYS.testMasters
);

export const useTestMasters = hooks.useList;
export const useCreateTestMaster = hooks.useCreate;
export const useUpdateTestMaster = hooks.useUpdate;
export const useDeleteTestMaster = hooks.useDelete;

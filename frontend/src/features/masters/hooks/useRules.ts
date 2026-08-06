/**
 * Rule master query hooks.
 *
 * Rules are the leaf of the hierarchy — nothing displays a rule's label, so there
 * are no dependent caches to invalidate.
 */

import { ruleApi } from '../api/ruleApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type {
  CreateRuleRequest,
  Rule,
  RuleListParams,
  UpdateRuleRequest,
} from '../models/Rule';

const hooks = createMasterHooks<
  Rule,
  CreateRuleRequest,
  UpdateRuleRequest,
  RuleListParams
>(ruleApi, MASTER_KEYS.rules);

export const useRules = hooks.useList;
export const useCreateRule = hooks.useCreate;
export const useUpdateRule = hooks.useUpdate;
export const useDeleteRule = hooks.useDelete;

/**
 * Rule master API calls.
 * Maps to backend: /api/v1/masters/rules
 */

import { createMasterApi } from './createMasterApi';
import type {
  CreateRuleRequest,
  Rule,
  RuleListParams,
  UpdateRuleRequest,
} from '../models/Rule';

export const ruleApi = createMasterApi<
  Rule,
  CreateRuleRequest,
  UpdateRuleRequest,
  RuleListParams
>('/masters/rules', 'rules');

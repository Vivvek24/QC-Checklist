import { questionApi } from '../api/questionApi';
import { createMasterHooks } from './createMasterHooks';
import { MASTER_KEYS } from './masterQueryKeys';
import type { Question, QuestionListParams, CreateQuestionRequest, UpdateQuestionRequest } from '../models/Question';

const hooks = createMasterHooks<Question, CreateQuestionRequest, UpdateQuestionRequest, QuestionListParams>(
  questionApi, MASTER_KEYS.questions
);

export const useQuestions = hooks.useList;
export const useCreateQuestion = hooks.useCreate;
export const useUpdateQuestion = hooks.useUpdate;
export const useDeleteQuestion = hooks.useDelete;

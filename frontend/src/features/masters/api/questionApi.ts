import { createMasterApi } from './createMasterApi';
import type { Question, QuestionListParams, CreateQuestionRequest, UpdateQuestionRequest } from '../models/Question';

export const questionApi = createMasterApi<Question, CreateQuestionRequest, UpdateQuestionRequest, QuestionListParams>(
  '/masters/questions', 'items'
);

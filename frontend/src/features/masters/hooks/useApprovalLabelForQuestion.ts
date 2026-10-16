/**
 * useApprovalLabelForQuestion — approval-label management for the Question form.
 *
 * Mirrors the Stage approval-label flow but keyed by question_id. Owns the
 * locally-edited label list (synced to the server on save by QuestionPage), the
 * add/edit label sub-form, and the dialog open/close state. QuestionForm just
 * renders the UI from what this hook returns.
 */

import { useCallback, useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { approvalLabelApi } from '../api/approvalLabelApi';
import { useRoles } from '@features/user-management/hooks/useRoles';

/** A locally-edited approval label (before it's synced to the server on save). */
export interface LocalLabel {
  tempId: string;
  id?: number;
  label: string;
  role_ids: number[];
  is_active: boolean;
}

const labelSchema = z.object({
  label: z.string().min(1, 'Label is required').max(255),
  role_ids: z.array(z.number()),
  is_active: z.boolean(),
});
export type LabelFormData = z.infer<typeof labelSchema>;
const LABEL_EMPTY: LabelFormData = { label: '', role_ids: [], is_active: true };

let labelTempCounter = 0;

export const useApprovalLabelForQuestion = () => {
  const { roleOptions } = useRoles();
  const roleMap = Object.fromEntries(roleOptions.map((r) => [r.value, r.label]));

  const [localLabels, setLocalLabels] = useState<LocalLabel[]>([]);
  const [labelDialogOpen, setLabelDialogOpen] = useState(false);
  const [editingLabelIdx, setEditingLabelIdx] = useState<number | null>(null);

  const {
    register,
    handleSubmit,
    control,
    reset: resetLabelForm,
    formState: { errors },
  } = useForm<LabelFormData>({ resolver: zodResolver(labelSchema), defaultValues: LABEL_EMPTY });

  /** Load the question's existing labels into the local list (edit mode). */
  const loadLabels = useCallback(async (questionId: number) => {
    try {
      const result = await approvalLabelApi.list({ question_id: questionId });
      setLocalLabels(result.items.map((l) => ({
        tempId: `ex-${l.id}`, id: Number(l.id),
        label: l.label, role_ids: l.role_ids, is_active: l.is_active,
      })));
    } catch {
      setLocalLabels([]);
    }
  }, []);

  /** Reset all local label state (on panel close / create mode). */
  const resetLabels = useCallback(() => {
    setLocalLabels([]);
    setLabelDialogOpen(false);
    setEditingLabelIdx(null);
  }, []);

  const openCreateLabel = () => {
    setEditingLabelIdx(null);
    resetLabelForm(LABEL_EMPTY);
    setLabelDialogOpen(true);
  };

  const openEditLabel = (idx: number) => {
    const lbl = localLabels[idx]!;
    setEditingLabelIdx(idx);
    resetLabelForm({ label: lbl.label, role_ids: lbl.role_ids, is_active: lbl.is_active });
    setLabelDialogOpen(true);
  };

  const deleteLabel = (idx: number) => setLocalLabels((prev) => prev.filter((_, i) => i !== idx));

  const closeLabelDialog = () => { setLabelDialogOpen(false); setEditingLabelIdx(null); };

  const saveLabelLocal = (data: LabelFormData) => {
    if (editingLabelIdx !== null) {
      setLocalLabels((prev) => prev.map((l, i) => i === editingLabelIdx
        ? { ...l, label: data.label.trim(), role_ids: data.role_ids, is_active: data.is_active }
        : l));
    } else {
      setLocalLabels((prev) => [...prev, {
        tempId: `new-${++labelTempCounter}`, label: data.label.trim(), role_ids: data.role_ids, is_active: data.is_active,
      }]);
    }
    closeLabelDialog();
  };

  /** The labels to send up in the submit payload (id present = update, absent = create). */
  const toPayload = () =>
    localLabels.map((l) => ({ id: l.id, label: l.label, role_ids: l.role_ids, is_active: l.is_active }));

  return {
    // role options for the MultiSelect + a lookup for the labels table
    roleOptions,
    roleMap,
    // local label list + dialog state
    localLabels,
    labelDialogOpen,
    editingLabelIdx,
    // label sub-form bindings
    register,
    control,
    errors,
    // actions
    loadLabels,
    resetLabels,
    openCreateLabel,
    openEditLabel,
    deleteLabel,
    closeLabelDialog,
    submitLabel: handleSubmit(saveLabelLocal),
    toPayload,
  };
};

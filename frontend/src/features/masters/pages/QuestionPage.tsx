import { useRef, useState } from 'react';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import { Tag } from 'primereact/tag';
import { Toast } from 'primereact/toast';
import type { DataTableFilterMeta } from 'primereact/datatable';
import { QuestionForm } from '../components/QuestionForm';
import { MasterCrudPage } from '../components/MasterCrudPage';
import { MasterRowActions } from '../components/MasterRowActions';
import { MasterStatusTag } from '../components/MasterStatusTag';
import { useQuestions, useCreateQuestion, useUpdateQuestion, useDeleteQuestion } from '../hooks/useQuestions';
import { useMasterPermissions } from '../hooks/useMasterPermissions';
import { questionOptionApi } from '../api/questionOptionApi';
import type { Question } from '../models/Question';

const defaultFilters: DataTableFilterMeta = {
  title: { value: null, matchMode: FilterMatchMode.CONTAINS },
};

const BoolBadge = ({ value }: { value: boolean }) => (
  <Tag value={value ? 'Yes' : 'No'} severity={value ? 'success' : 'danger'} />
);

export const QuestionPage = () => {
  const [filters, setFilters] = useState<DataTableFilterMeta>(defaultFilters);
  const { data, isLoading, refetch, isRefetching } = useQuestions();
  const createMutation = useCreateQuestion();
  const updateMutation = useUpdateQuestion();
  const deleteMutation = useDeleteQuestion();
  const permissions = useMasterPermissions('questions');

  const toast = useRef<Toast>(null);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [editing, setEditing] = useState<Question | null>(null);
  const [formSaving, setFormSaving] = useState(false);

  const openCreate = () => { setEditing(null); setDialogVisible(true); };
  const openEdit = (row: Question) => { setEditing(row); setDialogVisible(true); };
  const closeDialog = () => { setDialogVisible(false); setEditing(null); };

  const handleDelete = async (row: Question) => {
    try {
      await deleteMutation.mutateAsync(String(row.id));
      toast.current?.show({ severity: 'success', summary: 'Deleted', life: 3000 });
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Delete failed', life: 5000 });
    }
  };

  const handleSubmit = async (payload: any) => {
    setFormSaving(true);
    try {
      const { options, ...questionData } = payload;
      let questionId: number;

      if (editing) {
        await updateMutation.mutateAsync({ id: String(editing.id), request: questionData });
        questionId = Number(editing.id);
      } else {
        const created = await createMutation.mutateAsync(questionData);
        questionId = Number((created as any).id);
      }

      // Sync options via existing API
      if (options && options.length > 0) {
        const existingIds = new Set(options.filter((o: any) => o.id).map((o: any) => o.id));

        // Delete removed options (edit mode only)
        if (editing) {
          const serverOptions = await questionOptionApi.list({ question_id: questionId });
          for (const so of serverOptions.items) {
            if (!existingIds.has(Number(so.id))) {
              await questionOptionApi.remove(String(so.id));
            }
          }
        }

        // Create or update each option
        for (const opt of options) {
          if (opt.id) {
            await questionOptionApi.update(String(opt.id), {
              option_title: opt.option_title,
              is_response_option: opt.is_response_option ?? false,
              is_active: opt.is_active,
            });
          } else {
            await questionOptionApi.create({
              option_title: opt.option_title,
              is_response_option: opt.is_response_option ?? false,
              question_id: questionId,
              is_active: opt.is_active,
            });
          }
        }
      }

      toast.current?.show({ severity: 'success', summary: 'Success', detail: editing ? 'Question updated' : 'Question created', life: 3000 });
      closeDialog();
    } catch (e: any) {
      toast.current?.show({ severity: 'error', summary: 'Error', detail: e?.response?.data?.detail || 'Save failed', life: 5000 });
    } finally {
      setFormSaving(false);
    }
  };

  return (
    <MasterCrudPage<Question>
      title="Questions" subtitle="Manage question master data" newLabel="New Question"
      rows={data?.items ?? []} loading={isLoading || isRefetching} refreshing={isRefetching}
      onRefresh={() => refetch()} onNew={openCreate} canCreate={permissions.canCreate}
      filters={filters} onFilterChange={setFilters} emptyMessage="No questions defined yet." toastRef={toast}
      columns={
        <>
          <Column field="title" header="Title" sortable filter filterPlaceholder="Search..." style={{ minWidth: '14rem' }} />
          <Column field="answer_type" header="Answer Type" sortable body={(row: Question) => <Tag value={row.answer_type} severity="info" />} style={{ width: '12rem' }} />
          <Column header="Text Box" body={(row: Question) => <BoolBadge value={row.has_text_box} />} style={{ width: '6rem' }} />
          <Column header="Sub Q." body={(row: Question) => <BoolBadge value={row.has_sub_question} />} style={{ width: '6rem' }} />
          <Column header="Validation" body={(row: Question) => <BoolBadge value={row.is_validation_required} />} style={{ width: '6rem' }} />
          <Column header="Resp. Opt." body={(row: Question) => <BoolBadge value={row.has_response_option} />} style={{ width: '6rem' }} />
          <Column header="Multi" body={(row: Question) => <BoolBadge value={row.allow_multiple_input} />} style={{ width: '5rem' }} />
          <Column header="Calc." body={(row: Question) => <BoolBadge value={row.is_calculated} />} style={{ width: '5rem' }} />
          <Column header="Status" body={(row: Question) => <MasterStatusTag isActive={row.is_active} />} style={{ width: '7rem' }} />
          {permissions.canModifyRows && (
            <Column header="Actions" body={(row: Question) => (
              <MasterRowActions label={row.title} canUpdate={permissions.canUpdate} canDelete={permissions.canDelete}
                onEdit={() => openEdit(row)} onDelete={() => handleDelete(row)} />
            )} style={{ width: '7rem' }} />
          )}
        </>
      }
    >
      <QuestionForm visible={dialogVisible} question={editing} saving={formSaving}
        onHide={closeDialog} onSubmit={handleSubmit} />
    </MasterCrudPage>
  );
};

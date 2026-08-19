"""
SQLAlchemy ORM Models.

All models must be imported here so that SQLAlchemy's Base.metadata
can resolve foreign key relationships between tables at startup.
"""

from src.infrastructure.database.models.approval_matrix_model import (  # noqa: F401
    ApprovalAssignmentModel,
    ApprovalMatrixModel,
    ApprovalRuleModel,
    ApprovalTaskModel,
)
from src.infrastructure.database.models.audit_log_model import AuditLogModel  # noqa: F401
from src.infrastructure.database.models.base_model import Base, BaseModel  # noqa: F401
from src.infrastructure.database.models.masters.approval_label_model import ApprovalLabelModel, ApprovalLabelUserRoleModel  # noqa: F401
from src.infrastructure.database.models.masters.business_unit_model import BusinessUnitModel  # noqa: F401
from src.infrastructure.database.models.masters.format_model import FormatModel  # noqa: F401
from src.infrastructure.database.models.masters.product_model import ProductModel  # noqa: F401
from src.infrastructure.database.models.masters.question_model import QuestionModel, QuestionSubQuestionModel  # noqa: F401
from src.infrastructure.database.models.masters.remark_model import RemarkModel, RemarkUserRoleModel  # noqa: F401
from src.infrastructure.database.models.masters.sap_field_model import SapFieldModel  # noqa: F401
from src.infrastructure.database.models.masters.stage_model import StageModel  # noqa: F401
from src.infrastructure.database.models.masters.unit_model import UnitModel  # noqa: F401
from src.infrastructure.database.models.masters.validation_type_model import ValidationTypeModel  # noqa: F401
from src.infrastructure.database.models.role_model import (  # noqa: F401
    PermissionModel,
    RoleAssignmentModel,
    RoleModel,
    RolePermissionModel,
)
from src.infrastructure.database.models.tenant_model import TenantModel  # noqa: F401
from src.infrastructure.database.models.user_details_model import UserDetailsModel  # noqa: F401
from src.infrastructure.database.models.user_model import UserModel  # noqa: F401

# ─── Masters (continued) ───
from src.infrastructure.database.models.masters.format_stage_mapping_model import FormatStageMappingModel  # noqa: F401
from src.infrastructure.database.models.masters.section_model import SectionModel  # noqa: F401
from src.infrastructure.database.models.masters.stage_question_mapping_model import StageQuestionMappingModel  # noqa: F401
from src.infrastructure.database.models.masters.question_option_model import QuestionOptionModel  # noqa: F401
from src.infrastructure.database.models.masters.test_master_model import TestMasterModel  # noqa: F401

# ─── QC Checklist ───
from src.infrastructure.database.models.qc_checklist.checklist_request_model import ChecklistRequestModel  # noqa: F401
from src.infrastructure.database.models.qc_checklist.checklist_stage_model import ChecklistStageModel  # noqa: F401
from src.infrastructure.database.models.qc_checklist.checklist_stage_section_model import ChecklistStageSectionModel  # noqa: F401
from src.infrastructure.database.models.qc_checklist.stage_approval_label_mapping_model import StageApprovalLabelMappingModel  # noqa: F401
from src.infrastructure.database.models.qc_checklist.question_answer_model import QuestionAnswerModel  # noqa: F401
from src.infrastructure.database.models.qc_checklist.question_answer_helper_model import QuestionAnswerHelperModel  # noqa: F401
from src.infrastructure.database.models.qc_checklist.question_answer_sub_question_answer_model import QuestionAnswerSubQuestionAnswerModel  # noqa: F401

# ─── Workflow engine ───
from src.infrastructure.database.models.workflow_model import (  # noqa: F401
    WorkflowDefinitionModel,
    WorkflowHistoryModel,
    WorkflowInstanceModel,
    WorkflowStatusModel,
    WorkflowTransitionModel,
)

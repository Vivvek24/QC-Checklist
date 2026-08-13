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

# ─── Workflow engine ───
from src.infrastructure.database.models.workflow_model import (  # noqa: F401
    WorkflowDefinitionModel,
    WorkflowHistoryModel,
    WorkflowInstanceModel,
    WorkflowStatusModel,
    WorkflowTransitionModel,
)

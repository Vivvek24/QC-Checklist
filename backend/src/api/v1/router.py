"""
API v1 Router - aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter

from src.api.v1.endpoints.approval_matrix_controller import router as approval_matrix_router
from src.api.v1.endpoints.auth_controller import router as auth_router
from src.api.v1.endpoints.employee_ad_controller import router as employee_ad_router
from src.api.v1.endpoints.employee_import_controller import router as employee_import_router
from src.api.v1.endpoints.health_controller import router as health_router
from src.api.v1.endpoints.masters.approval_label_controller import router as approval_label_master_router
from src.api.v1.endpoints.masters.business_unit_controller import router as business_unit_router
from src.api.v1.endpoints.masters.format_controller import router as format_router
from src.api.v1.endpoints.masters.format_stage_mapping_controller import router as format_stage_mapping_router
from src.api.v1.endpoints.masters.product_controller import router as product_router
from src.api.v1.endpoints.masters.test_master_controller import router as test_master_router
from src.api.v1.endpoints.masters.question_controller import router as question_router
from src.api.v1.endpoints.masters.question_option_controller import router as question_option_router
from src.api.v1.endpoints.masters.remark_controller import router as remark_router
from src.api.v1.endpoints.masters.sap_field_controller import router as sap_field_router
from src.api.v1.endpoints.masters.section_controller import router as section_router
from src.api.v1.endpoints.masters.stage_controller import router as stage_router
from src.api.v1.endpoints.masters.stage_question_mapping_controller import router as stage_question_mapping_router
from src.api.v1.endpoints.masters.unit_controller import router as unit_router
from src.api.v1.endpoints.masters.validation_type_controller import router as validation_type_router
from src.api.v1.endpoints.rbac_controller import router as rbac_router
from src.api.v1.endpoints.user_controller import router as user_router
from src.api.v1.endpoints.workflow_controller import router as workflow_router
from src.api.v1.endpoints.workflow_instance_controller import (
    router as workflow_instance_router,
)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(rbac_router)
api_v1_router.include_router(employee_import_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(employee_ad_router)

# ─── Masters ───
api_v1_router.include_router(business_unit_router)
api_v1_router.include_router(approval_label_master_router)
api_v1_router.include_router(unit_router)
api_v1_router.include_router(format_router)
api_v1_router.include_router(format_stage_mapping_router)
api_v1_router.include_router(stage_router)
api_v1_router.include_router(stage_question_mapping_router)
api_v1_router.include_router(question_router)
api_v1_router.include_router(question_option_router)
api_v1_router.include_router(product_router)
api_v1_router.include_router(test_master_router)
api_v1_router.include_router(validation_type_router)
api_v1_router.include_router(remark_router)
api_v1_router.include_router(sap_field_router)
api_v1_router.include_router(section_router)

# ─── Workflow engine ───
api_v1_router.include_router(approval_matrix_router)
api_v1_router.include_router(workflow_router)
api_v1_router.include_router(workflow_instance_router)

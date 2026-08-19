"""
Seed script for RBAC permissions.
Idempotent — re-running skips existing records.
Usage: python -m scripts.seed_rbac
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.infrastructure.database.models.role_model import (
    PermissionModel,
    RoleAssignmentModel,
    RoleModel,
    RolePermissionModel,
)
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.database.unit_of_work import UnitOfWork

_PERMISSION_TABLE = [
    # ─── Menu permissions ───
    ("menu.dashboard",      "MENU",  "dashboard",      "READ",    "Dashboard Menu"),
    ("menu.users",          "MENU",  "users",          "READ",    "Users Menu"),
    ("menu.roles",          "MENU",  "roles",          "READ",    "Roles Menu"),
    ("menu.audit_logs",     "MENU",  "audit_logs",     "READ",    "Audit Logs Menu"),
    ("menu.services",       "MENU",  "services",       "READ",    "Services Menu"),
    ("menu.workflows",      "MENU",  "workflows",      "READ",    "Workflows Menu"),
    ("menu.masters",        "MENU",  "masters",        "READ",    "Masters Menu"),
    ("menu.masters.business_units", "MENU", "masters.business_units", "READ", "Business Units Menu"),
    ("menu.masters.units",  "MENU",  "masters.units",  "READ",    "Units Menu"),
    ("menu.masters.formats","MENU",  "masters.formats","READ",    "Formats Menu"),
    ("menu.masters.stages", "MENU",  "masters.stages", "READ",    "Stages Menu"),
    ("menu.masters.questions","MENU","masters.questions","READ",  "Questions Menu"),
    ("menu.masters.products","MENU","masters.products","READ",   "Products Menu"),
    ("menu.masters.validation_types","MENU","masters.validation_types","READ","Validation Types Menu"),
    ("menu.masters.remarks","MENU","masters.remarks","READ",    "Remarks Menu"),
    ("menu.masters.sap_fields","MENU","masters.sap_fields","READ","SAP Fields Menu"),
    ("menu.masters.approval_labels","MENU","masters.approval_labels","READ","Approval Labels Menu"),
    ("menu.masters.stage_question_mapping","MENU","masters.stage_question_mapping","READ","Stage Question Mapping Menu"),
    ("menu.masters.formats_view","MENU","masters.formats_view","READ","Formats View Menu"),
    # ─── User management ───
    ("users.list",          "API",   "users",          "READ",    "List Users"),
    ("users.create",        "API",   "users",          "CREATE",  "Create User"),
    ("users.update",        "API",   "users",          "UPDATE",  "Update User"),
    ("users.delete",        "API",   "users",          "DELETE",  "Delete User"),
    ("users.export",        "API",   "users",          "EXPORT",  "Export Users"),
    ("users.import",        "API",   "users",          "IMPORT",  "Import Users"),
    # ─── Role management ───
    ("roles.list",          "API",   "roles",          "READ",    "List Roles"),
    ("roles.create",        "API",   "roles",          "CREATE",  "Create Role"),
    ("roles.update",        "API",   "roles",          "UPDATE",  "Update Role"),
    ("roles.assign",        "API",   "roles",          "EXECUTE", "Assign Roles"),
    ("audit.read",          "API",   "audit_logs",     "READ",    "View Audit Logs"),
    # ─── RBAC management ───
    ("rbac.read",           "API",   "rbac",           "READ",    "View Roles & Permissions"),
    ("rbac.create",         "API",   "rbac",           "CREATE",  "Create Roles & Permissions"),
    ("rbac.update",         "API",   "rbac",           "UPDATE",  "Update Roles & Permissions"),
    # ─── Services ───
    ("services.employee_ad","API",   "services",       "EXECUTE", "Access Employee AD Service"),
    # ─── Business Unit master ───
    ("business_units.list",   "API", "business_units", "READ",    "List Business Units"),
    ("business_units.create", "API", "business_units", "CREATE",  "Create Business Unit"),
    ("business_units.update", "API", "business_units", "UPDATE",  "Update Business Unit"),
    ("business_units.delete", "API", "business_units", "DELETE",  "Delete Business Unit"),
    # ─── Unit master ───
    ("units.list",            "API", "units",          "READ",    "List Units"),
    ("units.create",          "API", "units",          "CREATE",  "Create Unit"),
    ("units.update",          "API", "units",          "UPDATE",  "Update Unit"),
    ("units.delete",          "API", "units",          "DELETE",  "Delete Unit"),
    # ─── Format master ───
    ("formats.list",          "API", "formats",        "READ",    "List Formats"),
    ("formats.create",        "API", "formats",        "CREATE",  "Create Format"),
    ("formats.update",        "API", "formats",        "UPDATE",  "Update Format"),
    ("formats.delete",        "API", "formats",        "DELETE",  "Delete Format"),
    # ─── Stage master ───
    ("stages.list",           "API", "stages",         "READ",    "List Stages"),
    ("stages.create",         "API", "stages",         "CREATE",  "Create Stage"),
    ("stages.update",         "API", "stages",         "UPDATE",  "Update Stage"),
    ("stages.delete",         "API", "stages",         "DELETE",  "Delete Stage"),
    # ─── Question master ───
    ("questions.list",        "API", "questions",      "READ",    "List Questions"),
    ("questions.create",      "API", "questions",      "CREATE",  "Create Question"),
    ("questions.update",      "API", "questions",      "UPDATE",  "Update Question"),
    ("questions.delete",      "API", "questions",      "DELETE",  "Delete Question"),
    # ─── Product master ───
    ("products.list",         "API", "products",       "READ",    "List Products"),
    ("products.create",       "API", "products",       "CREATE",  "Create Product"),
    ("products.update",       "API", "products",       "UPDATE",  "Update Product"),
    ("products.delete",       "API", "products",       "DELETE",  "Delete Product"),
    # ─── Validation Type master ───
    ("validation_types.list",  "API", "validation_types","READ",  "List Validation Types"),
    ("validation_types.create","API", "validation_types","CREATE","Create Validation Type"),
    ("validation_types.update","API", "validation_types","UPDATE","Update Validation Type"),
    ("validation_types.delete","API", "validation_types","DELETE","Delete Validation Type"),
    # ─── Remark master ───
    ("remarks.list",           "API", "remarks",        "READ",   "List Remarks"),
    ("remarks.create",         "API", "remarks",        "CREATE", "Create Remark"),
    ("remarks.update",         "API", "remarks",        "UPDATE", "Update Remark"),
    ("remarks.delete",         "API", "remarks",        "DELETE", "Delete Remark"),
    # ─── SAP Field master ───
    ("sap_fields.list",        "API", "sap_fields",     "READ",   "List SAP Fields"),
    ("sap_fields.create",      "API", "sap_fields",     "CREATE", "Create SAP Field"),
    ("sap_fields.update",      "API", "sap_fields",     "UPDATE", "Update SAP Field"),
    ("sap_fields.delete",      "API", "sap_fields",     "DELETE", "Delete SAP Field"),
    # ─── Approval Label master ───
    ("approval_labels.list",   "API", "approval_labels","READ",   "List Approval Labels"),
    ("approval_labels.create", "API", "approval_labels","CREATE", "Create Approval Label"),
    ("approval_labels.update", "API", "approval_labels","UPDATE", "Update Approval Label"),
    ("approval_labels.delete", "API", "approval_labels","DELETE", "Delete Approval Label"),
    # ─── Question Option master ───
    ("question_options.list",   "API", "question_options", "READ",   "List Question Options"),
    ("question_options.create", "API", "question_options", "CREATE", "Create Question Option"),
    ("question_options.update", "API", "question_options", "UPDATE", "Update Question Option"),
    ("question_options.delete", "API", "question_options", "DELETE", "Delete Question Option"),
    # ─── Section master ───
    ("sections.list",   "API", "sections", "READ",   "List Sections"),
    ("sections.create", "API", "sections", "CREATE", "Create Section"),
    ("sections.update", "API", "sections", "UPDATE", "Update Section"),
    ("sections.delete", "API", "sections", "DELETE", "Delete Section"),
    # ─── Format Stage Mapping ───
    ("format_stage_mappings.list",   "API", "format_stage_mappings", "READ",   "List Format Stage Mappings"),
    ("format_stage_mappings.create", "API", "format_stage_mappings", "CREATE", "Create Format Stage Mapping"),
    ("format_stage_mappings.update", "API", "format_stage_mappings", "UPDATE", "Update Format Stage Mapping"),
    ("format_stage_mappings.delete", "API", "format_stage_mappings", "DELETE", "Delete Format Stage Mapping"),
    # ─── Stage Question Mapping ───
    ("stage_question_mappings.list",   "API", "stage_question_mappings", "READ",   "List Stage Question Mappings"),
    ("stage_question_mappings.create", "API", "stage_question_mappings", "CREATE", "Create Stage Question Mapping"),
    ("stage_question_mappings.update", "API", "stage_question_mappings", "UPDATE", "Update Stage Question Mapping"),
    ("stage_question_mappings.delete", "API", "stage_question_mappings", "DELETE", "Delete Stage Question Mapping"),
    # ─── Test Master ───
    ("test_masters.list",   "API", "test_masters", "READ",   "List Test Masters"),
    ("test_masters.create", "API", "test_masters", "CREATE", "Create Test Master"),
    ("test_masters.update", "API", "test_masters", "UPDATE", "Update Test Master"),
    ("test_masters.delete", "API", "test_masters", "DELETE", "Delete Test Master"),
    # ─── QC Checklist ───
    ("menu.qc_checklist",              "MENU", "qc_checklist",        "READ",   "Create Request Page"),
    ("dashboard.read",                 "API", "dashboard",            "READ",   "View Dashboard Data"),
    ("checklist_requests.list",        "API", "checklist_requests",   "READ",   "List Checklist Requests"),
    ("checklist_requests.create",      "API", "checklist_requests",   "CREATE", "Create Checklist Request"),
    ("checklist_requests.update",      "API", "checklist_requests",   "UPDATE", "Update Checklist Request"),
    ("checklist_requests.delete",      "API", "checklist_requests",   "DELETE", "Delete Checklist Request"),
    ("checklist_stages.list",          "API", "checklist_stages",     "READ",   "List Checklist Stages"),
    ("checklist_stages.create",        "API", "checklist_stages",     "CREATE", "Create Checklist Stage"),
    ("checklist_stages.update",        "API", "checklist_stages",     "UPDATE", "Update Checklist Stage"),
    ("checklist_stages.delete",        "API", "checklist_stages",     "DELETE", "Delete Checklist Stage"),
    ("checklist_stage_sections.list",   "API", "checklist_stage_sections", "READ",   "List Checklist Stage Sections"),
    ("checklist_stage_sections.create", "API", "checklist_stage_sections", "CREATE", "Create Checklist Stage Section"),
    ("checklist_stage_sections.update", "API", "checklist_stage_sections", "UPDATE", "Update Checklist Stage Section"),
    ("checklist_stage_sections.delete", "API", "checklist_stage_sections", "DELETE", "Delete Checklist Stage Section"),
    ("stage_approval_label_mappings.list",   "API", "stage_approval_label_mappings", "READ",   "List Stage Approval Label Mappings"),
    ("stage_approval_label_mappings.create", "API", "stage_approval_label_mappings", "CREATE", "Create Stage Approval Label Mapping"),
    ("stage_approval_label_mappings.update", "API", "stage_approval_label_mappings", "UPDATE", "Update Stage Approval Label Mapping"),
    ("stage_approval_label_mappings.delete", "API", "stage_approval_label_mappings", "DELETE", "Delete Stage Approval Label Mapping"),
    ("question_answers.list",   "API", "question_answers", "READ",   "List Question Answers"),
    ("question_answers.create", "API", "question_answers", "CREATE", "Create Question Answer"),
    ("question_answers.update", "API", "question_answers", "UPDATE", "Update Question Answer"),
    ("question_answers.delete", "API", "question_answers", "DELETE", "Delete Question Answer"),
    ("question_answer_helpers.list",   "API", "question_answer_helpers", "READ",   "List Question Answer Helpers"),
    ("question_answer_helpers.create", "API", "question_answer_helpers", "CREATE", "Create Question Answer Helper"),
    ("question_answer_helpers.update", "API", "question_answer_helpers", "UPDATE", "Update Question Answer Helper"),
    ("question_answer_helpers.delete", "API", "question_answer_helpers", "DELETE", "Delete Question Answer Helper"),
    # ─── Workflow engine ───
    ("workflows.list",               "API", "workflows",          "READ",   "List Workflows"),
    ("workflows.create",             "API", "workflows",          "CREATE", "Create Workflow"),
    ("workflows.update",             "API", "workflows",          "UPDATE", "Update Workflow"),
    ("workflows.delete",             "API", "workflows",          "DELETE", "Delete Workflow"),
    ("workflow_instances.list",      "API", "workflow_instances", "READ",   "View Workflow Instances"),
    ("workflow_instances.create",    "API", "workflow_instances", "CREATE", "Start Workflow"),
    ("workflow_instances.update",    "API", "workflow_instances", "UPDATE", "Act on Workflow"),
    ("workflow_instances.delete",    "API", "workflow_instances", "DELETE", "Delete Instance"),
    ("approval_matrices.list",       "API", "approval_matrices",  "READ",   "List Approval Matrices"),
    ("approval_matrices.create",     "API", "approval_matrices",  "CREATE", "Create Approval Matrix"),
    ("approval_matrices.update",     "API", "approval_matrices",  "UPDATE", "Update Approval Matrix"),
    ("approval_matrices.delete",     "API", "approval_matrices",  "DELETE", "Delete Approval Matrix"),
    # ─── Field-level permissions ───
    ("users.salary.read",   "FIELD", "users.salary",   "READ",    "View Salary"),
    ("users.salary.update", "FIELD", "users.salary",   "UPDATE",  "Edit Salary"),
    ("users.email.read",    "FIELD", "users.email",    "READ",    "View Email"),
    ("users.email.update",  "FIELD", "users.email",    "UPDATE",  "Edit Email"),
    ("users.phone.read",    "FIELD", "users.phone",    "READ",    "View Phone"),
]

DEFAULT_PERMISSIONS = [
    {"code": c, "scope": s, "resource": r, "action": a, "name": n}
    for c, s, r, a, n in _PERMISSION_TABLE
]

# ADMINISTRATOR gets all permissions
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ADMINISTRATOR": [p["code"] for p in DEFAULT_PERMISSIONS],
}


async def seed() -> None:
    async with UnitOfWork() as uow:
        session = uow.session

        # 1. Ensure ADMINISTRATOR role exists
        r = (await session.execute(
            select(RoleModel).where(RoleModel.code == "ADMINISTRATOR")
        )).scalar_one_or_none()
        if not r:
            session.add(RoleModel(
                code="ADMINISTRATOR", name="Administrator",
                description="Full system access", is_system=True, is_active=True,
                created_by="seed_script", modified_by="seed_script",
            ))
            print("  [new]  Role 'ADMINISTRATOR' created")
        else:
            print("  [skip] Role 'ADMINISTRATOR' already exists")
        await session.flush()

        # 2. Upsert permissions, collect id map
        perm_map: dict[str, int] = {}
        for p in DEFAULT_PERMISSIONS:
            perm = (await session.execute(
                select(PermissionModel).where(PermissionModel.code == p["code"])
            )).scalar_one_or_none()
            if perm:
                perm_map[p["code"]] = perm.id
                print(f"  [skip] Permission '{p['code']}' already exists")
            else:
                new_perm = PermissionModel(
                    code=p["code"], name=p["name"], description="",
                    scope=p["scope"], resource=p["resource"], action=p["action"],
                    is_active=True, created_by="seed_script", modified_by="seed_script",
                )
                session.add(new_perm)
                await session.flush()
                perm_map[p["code"]] = new_perm.id
                print(f"  [new]  Permission '{p['code']}' created")

        # 3. Link all permissions to ADMINISTRATOR
        role = (await session.execute(
            select(RoleModel).where(RoleModel.code == "ADMINISTRATOR")
        )).scalar_one_or_none()

        if role:
            for perm_code in ROLE_PERMISSIONS["ADMINISTRATOR"]:
                perm_id = perm_map.get(perm_code)
                if perm_id is None:
                    continue
                exists = (await session.execute(
                    select(RolePermissionModel).where(
                        RolePermissionModel.role_id == role.id,
                        RolePermissionModel.permission_id == perm_id,
                    )
                )).scalar_one_or_none()
                if exists:
                    continue
                session.add(RolePermissionModel(
                    role_id=role.id, permission_id=perm_id,
                    created_by="seed_script", modified_by="seed_script",
                ))
                print(f"  [link] ADMINISTRATOR <- {perm_code}")

        await uow.commit()
        print("\nOK RBAC seed complete.")

    # 4. Assign ADMINISTRATOR role to users without any role assignment
    async with UnitOfWork() as uow:
        session = uow.session
        print("\nAssigning ADMINISTRATOR role to users without role assignments...")
        admin_role = (await session.execute(
            select(RoleModel).where(RoleModel.code == "ADMINISTRATOR")
        )).scalar_one_or_none()
        if not admin_role:
            print("  [warn] ADMINISTRATOR role not found")
            return

        users = (await session.execute(select(UserModel))).scalars().all()
        for user in users:
            existing = (await session.execute(
                select(RoleAssignmentModel).where(RoleAssignmentModel.user_id == user.id).limit(1)
            )).scalar_one_or_none()
            if existing:
                print(f"  [skip] User '{user.username}' already has a role assignment")
                continue
            session.add(RoleAssignmentModel(
                user_id=user.id, role_id=admin_role.id,
                tenant_id=None, is_active=True,
                created_by="seed_script", modified_by="seed_script",
            ))
            print(f"  [new]  User '{user.username}' -> Role 'ADMINISTRATOR'")

        await uow.commit()
        print("\nOK Role assignments complete.")


if __name__ == "__main__":
    print("Seeding RBAC permissions...")
    asyncio.run(seed())

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
    ("menu.dashboard",                 "MENU",  "dashboard",               "READ",    "Dashboard Menu"),
    ("menu.users",                     "MENU",  "users",                   "READ",    "Users Menu"),
    ("menu.roles",                     "MENU",  "roles",                   "READ",    "Roles Menu"),
    ("menu.audit_logs",                "MENU",  "audit_logs",              "READ",    "Audit Logs Menu"),
    ("menu.services",                  "MENU",  "services",                "READ",    "Services Menu"),
    ("menu.workflows",                 "MENU",  "workflows",               "READ",    "Workflows Menu"),
    ("menu.masters",                   "MENU",  "masters",                 "READ",    "Masters Menu"),
    ("menu.masters.countries",         "MENU",  "masters.countries",       "READ",    "Countries Menu"),
    ("menu.masters.states",            "MENU",  "masters.states",          "READ",    "States Menu"),
    ("menu.masters.categories_of_law", "MENU",  "masters.categories_of_law", "READ", "Categories of Law Menu"),
    ("menu.masters.legislations",      "MENU",  "masters.legislations",    "READ",    "Legislations Menu"),
    ("menu.masters.rules",             "MENU",  "masters.rules",           "READ",    "Rules Menu"),
    ("menu.masters.task_types",        "MENU",  "masters.task_types",      "READ",    "Task Types Menu"),
    ("users.list",                     "API",   "users",                   "READ",    "List Users"),
    ("users.create",                   "API",   "users",                   "CREATE",  "Create User"),
    ("users.update",                   "API",   "users",                   "UPDATE",  "Update User"),
    ("users.delete",                   "API",   "users",                   "DELETE",  "Delete User"),
    ("users.export",                   "API",   "users",                   "EXPORT",  "Export Users"),
    ("users.import",                   "API",   "users",                   "IMPORT",  "Import Users"),
    ("roles.list",                     "API",   "roles",                   "READ",    "List Roles"),
    ("roles.create",                   "API",   "roles",                   "CREATE",  "Create Role"),
    ("roles.update",                   "API",   "roles",                   "UPDATE",  "Update Role"),
    ("roles.assign",                   "API",   "roles",                   "EXECUTE", "Assign Roles"),
    ("audit.read",                     "API",   "audit_logs",              "READ",    "View Audit Logs"),
    ("rbac.read",                      "API",   "rbac",                    "READ",    "View Roles & Permissions"),
    ("rbac.create",                    "API",   "rbac",                    "CREATE",  "Create Roles & Permissions"),
    ("rbac.update",                    "API",   "rbac",                    "UPDATE",  "Update Roles & Permissions"),
    ("services.employee_ad",           "API",   "services",                "EXECUTE", "Access Employee AD Service"),
    ("countries.list",                 "API",   "countries",               "READ",    "List Countries"),
    ("countries.create",               "API",   "countries",               "CREATE",  "Create Country"),
    ("countries.update",               "API",   "countries",               "UPDATE",  "Update Country"),
    ("countries.delete",               "API",   "countries",               "DELETE",  "Delete Country"),
    ("states.list",                    "API",   "states",                  "READ",    "List States"),
    ("states.create",                  "API",   "states",                  "CREATE",  "Create State"),
    ("states.update",                  "API",   "states",                  "UPDATE",  "Update State"),
    ("states.delete",                  "API",   "states",                  "DELETE",  "Delete State"),
    ("categories_of_law.list",         "API",   "categories_of_law",       "READ",    "List Categories of Law"),
    ("categories_of_law.create",       "API",   "categories_of_law",       "CREATE",  "Create Category of Law"),
    ("categories_of_law.update",       "API",   "categories_of_law",       "UPDATE",  "Update Category of Law"),
    ("categories_of_law.delete",       "API",   "categories_of_law",       "DELETE",  "Delete Category of Law"),
    ("legislations.list",              "API",   "legislations",            "READ",    "List Legislations"),
    ("legislations.create",            "API",   "legislations",            "CREATE",  "Create Legislation"),
    ("legislations.update",            "API",   "legislations",            "UPDATE",  "Update Legislation"),
    ("legislations.delete",            "API",   "legislations",            "DELETE",  "Delete Legislation"),
    ("rules.list",                     "API",   "rules",                   "READ",    "List Rules"),
    ("rules.create",                   "API",   "rules",                   "CREATE",  "Create Rule"),
    ("rules.update",                   "API",   "rules",                   "UPDATE",  "Update Rule"),
    ("rules.delete",                   "API",   "rules",                   "DELETE",  "Delete Rule"),
    ("task_types.list",                "API",   "task_types",              "READ",    "List Task Types"),
    ("task_types.create",              "API",   "task_types",              "CREATE",  "Create Task Type"),
    ("task_types.update",              "API",   "task_types",              "UPDATE",  "Update Task Type"),
    ("task_types.delete",              "API",   "task_types",              "DELETE",  "Delete Task Type"),
    ("workflows.list",                 "API",   "workflows",               "READ",    "List Workflows"),
    ("workflows.create",               "API",   "workflows",               "CREATE",  "Create Workflow"),
    ("workflows.update",               "API",   "workflows",               "UPDATE",  "Update Workflow"),
    ("workflows.delete",               "API",   "workflows",               "DELETE",  "Delete Workflow"),
    ("workflow_instances.list",        "API",   "workflow_instances",      "READ",    "View Workflow Instances"),
    ("workflow_instances.create",      "API",   "workflow_instances",      "CREATE",  "Start Workflow"),
    ("workflow_instances.update",      "API",   "workflow_instances",      "UPDATE",  "Act on Workflow"),
    ("workflow_instances.delete",      "API",   "workflow_instances",      "DELETE",  "Delete Instance"),
    ("approval_matrices.list",         "API",   "approval_matrices",       "READ",    "List Approval Matrices"),
    ("approval_matrices.create",       "API",   "approval_matrices",       "CREATE",  "Create Approval Matrix"),
    ("approval_matrices.update",       "API",   "approval_matrices",       "UPDATE",  "Update Approval Matrix"),
    ("approval_matrices.delete",       "API",   "approval_matrices",       "DELETE",  "Delete Approval Matrix"),
    ("users.salary.read",              "FIELD", "users.salary",            "READ",    "View Salary"),
    ("users.salary.update",            "FIELD", "users.salary",            "UPDATE",  "Edit Salary"),
    ("users.email.read",               "FIELD", "users.email",             "READ",    "View Email"),
    ("users.email.update",             "FIELD", "users.email",             "UPDATE",  "Edit Email"),
    ("users.phone.read",               "FIELD", "users.phone",             "READ",    "View Phone"),
]

DEFAULT_PERMISSIONS = [
    {"code": c, "scope": s, "resource": r, "action": a, "name": n}
    for c, s, r, a, n in _PERMISSION_TABLE
]

ROLE_PERMISSIONS = {
    "ADMIN": [
        "menu.dashboard","menu.users","menu.roles","menu.audit_logs","menu.services",
        "users.list","users.create","users.update","users.delete","users.export","users.import",
        "roles.list","roles.create","roles.update","roles.assign","audit.read",
        "rbac.read","rbac.create","rbac.update","services.employee_ad",
        "menu.masters","menu.masters.countries","menu.masters.states",
        "menu.masters.categories_of_law","menu.masters.legislations",
        "menu.masters.rules","menu.masters.task_types",
        "countries.list","countries.create","countries.update","countries.delete",
        "states.list","states.create","states.update","states.delete",
        "categories_of_law.list","categories_of_law.create","categories_of_law.update","categories_of_law.delete",
        "legislations.list","legislations.create","legislations.update","legislations.delete",
        "rules.list","rules.create","rules.update","rules.delete",
        "task_types.list","task_types.create","task_types.update","task_types.delete",
        "menu.workflows",
        "workflows.list","workflows.create","workflows.update","workflows.delete",
        "workflow_instances.list","workflow_instances.create","workflow_instances.update","workflow_instances.delete",
        "approval_matrices.list","approval_matrices.create","approval_matrices.update","approval_matrices.delete",
        "users.salary.read","users.salary.update","users.email.read","users.email.update","users.phone.read",
    ],
    "MANAGER": [
        "menu.dashboard","menu.users","menu.services",
        "users.list","users.export","users.email.read","users.phone.read",
        "menu.masters","menu.masters.countries","menu.masters.states",
        "menu.masters.categories_of_law","menu.masters.legislations","menu.masters.rules","menu.masters.task_types",
        "countries.list","states.list","categories_of_law.list","legislations.list","rules.list","task_types.list",
        "menu.workflows","workflows.list",
        "workflow_instances.list","workflow_instances.create","workflow_instances.update",
        "approval_matrices.list",
    ],
    "USER": [
        "menu.dashboard","menu.services",
        "menu.masters","menu.masters.countries","menu.masters.states",
        "menu.masters.categories_of_law","menu.masters.legislations","menu.masters.rules","menu.masters.task_types",
        "countries.list","states.list","categories_of_law.list","legislations.list","rules.list","task_types.list",
        "menu.workflows","workflows.list","workflow_instances.list",
    ],
}


async def seed() -> None:
    async with UnitOfWork() as uow:
        session = uow.session
        # 1. Ensure system roles exist
        for role_code in ("ADMIN", "MANAGER", "USER"):
            r = (await session.execute(select(RoleModel).where(RoleModel.code == role_code))).scalar_one_or_none()
            if not r:
                session.add(RoleModel(
                    code=role_code, name=role_code.capitalize(),
                    description="", is_system=True, is_active=True,
                    created_by="seed_script", modified_by="seed_script",
                ))
        await session.flush()

        # 2. Upsert permissions, collect id map
        perm_map: dict[str, int] = {}
        for p in DEFAULT_PERMISSIONS:
            perm = (await session.execute(select(PermissionModel).where(PermissionModel.code == p["code"]))).scalar_one_or_none()
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

        # 3. Link permissions to roles
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = (await session.execute(select(RoleModel).where(RoleModel.code == role_code))).scalar_one_or_none()
            if not role:
                print(f"  [warn] Role '{role_code}' not found")
                continue

            for perm_code in perm_codes:
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
                print(f"  [link] {role_code} <- {perm_code}")

        await uow.commit()
        print("\nOK RBAC seed complete.")

    # 4. Assign ADMIN role to users without any assignment
    async with UnitOfWork() as uow:
        session = uow.session
        print("\nAssigning default role to existing users without role assignments...")
        admin_role = (await session.execute(select(RoleModel).where(RoleModel.code == "ADMIN"))).scalar_one_or_none()
        if not admin_role:
            print("  [warn] ADMIN role not found")
            return

        users = (await session.execute(select(UserModel))).scalars().all()
        for user in users:
            existing = (await session.execute(
                select(RoleAssignmentModel).where(RoleAssignmentModel.user_id == user.id)
            )).scalar_one_or_none()
            if existing:
                print(f"  [skip] User '{user.username}' already has a role")
                continue
            session.add(RoleAssignmentModel(
                user_id=user.id, role_id=admin_role.id,
                tenant_id=None, is_active=True,
                created_by="seed_script", modified_by="seed_script",
            ))
            print(f"  [new]  User '{user.username}' -> Role 'ADMIN'")

        await uow.commit()
        print("\nOK Role assignments complete.")


if __name__ == "__main__":
    print("Seeding RBAC permissions...")
    asyncio.run(seed())

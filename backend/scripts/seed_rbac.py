"""
Seed script for RBAC permissions.
Populates default menu, API, and field-level permissions.
Run via: python -m scripts.seed_rbac

This is idempotent — re-running will skip existing permissions.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.infrastructure.database.models.role_model import (
    PermissionModel,
    RoleAssignmentModel,
    RoleModel,
    RolePermissionModel,
)
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.database.session import async_session_factory

# ─── Default Permission Definitions ───
# Permission table — one row per line so it reads as a table rather than as
# 30-plus wrapped dict literals.
# Columns: (code, scope, resource, action, name)
_PERMISSION_TABLE = [
    # Menu permissions — control sidebar/navigation visibility
    ("menu.dashboard", "MENU", "dashboard", "READ", "Dashboard Menu"),
    ("menu.users", "MENU", "users", "READ", "Users Menu"),
    ("menu.roles", "MENU", "roles", "READ", "Roles Menu"),
    ("menu.audit_logs", "MENU", "audit_logs", "READ", "Audit Logs Menu"),
    ("menu.services", "MENU", "services", "READ", "Services Menu"),
    ("menu.published_services", "MENU", "published_services", "READ", "Published Services Menu"),
    ("menu.employees", "MENU", "employees", "READ", "Employees Menu"),
    ("menu.ldap", "MENU", "ldap", "READ", "LDAP Servers Menu"),
    # API permissions — control endpoint access
    ("users.list", "API", "users", "READ", "List Users"),
    ("users.create", "API", "users", "CREATE", "Create User"),
    ("users.update", "API", "users", "UPDATE", "Update User"),
    ("users.delete", "API", "users", "DELETE", "Delete User"),
    ("users.export", "API", "users", "EXPORT", "Export Users"),
    ("users.import", "API", "users", "IMPORT", "Import Users"),
    ("roles.list", "API", "roles", "READ", "List Roles"),
    ("roles.create", "API", "roles", "CREATE", "Create Role"),
    ("roles.update", "API", "roles", "UPDATE", "Update Role"),
    ("roles.assign", "API", "roles", "EXECUTE", "Assign Roles"),
    ("audit.read", "API", "audit_logs", "READ", "View Audit Logs"),
    # RBAC management permissions — granular control over roles & permissions CRUD
    ("rbac.read", "API", "rbac", "READ", "View Roles & Permissions"),
    ("rbac.create", "API", "rbac", "CREATE", "Create Roles & Permissions"),
    ("rbac.update", "API", "rbac", "UPDATE", "Update Roles & Permissions"),
    # Outbound/integration service permissions
    ("services.employee_ad", "API", "services", "EXECUTE", "Access Employee AD Service"),
    ("services.darwinbox", "API", "services", "EXECUTE", "Access Darwinbox Service"),
    ("services.ldap", "API", "services", "EXECUTE", "Access LDAP Service"),
    ("services.esigner", "API", "services", "EXECUTE", "Access E-Signer Service"),
    ("services.encryption", "API", "services", "EXECUTE", "Access Encryption Utility"),
    # Field-level permissions — control visibility of sensitive fields
    ("users.salary.read", "FIELD", "users.salary", "READ", "View Salary"),
    ("users.salary.update", "FIELD", "users.salary", "UPDATE", "Edit Salary"),
    ("users.email.read", "FIELD", "users.email", "READ", "View Email"),
    ("users.email.update", "FIELD", "users.email", "UPDATE", "Edit Email"),
    ("users.phone.read", "FIELD", "users.phone", "READ", "View Phone"),
]

# Expanded to the dict shape the seeding code below consumes.
DEFAULT_PERMISSIONS = [
    {"code": c, "scope": s, "resource": r, "action": a, "name": n}
    for c, s, r, a, n in _PERMISSION_TABLE
]

# Role → permission code assignments
ROLE_PERMISSIONS = {
    "ADMIN": [
        # Admin gets ALL permissions
        "menu.dashboard", "menu.users", "menu.roles", "menu.audit_logs",
        "menu.services",
        "menu.published_services",
        "menu.employees",
        "menu.ldap",
        "users.list", "users.create", "users.update", "users.delete",
        "users.export", "users.import",
        "roles.list", "roles.create", "roles.update", "roles.assign",
        "audit.read",
        "rbac.read", "rbac.create", "rbac.update", "services.employee_ad",
        "services.darwinbox", "services.ldap", "services.esigner",
        "services.encryption",
        "users.salary.read", "users.salary.update",
        "users.email.read", "users.email.update", "users.phone.read",
    ],
    "MANAGER": [
        "menu.dashboard", "menu.users", "menu.services",
        "users.list", "users.export",
        "users.email.read", "users.phone.read",
    ],
    "USER": [
        "menu.dashboard", "menu.services",
    ],
}


async def seed() -> None:
    """Seed default permissions and role-permission mappings."""
    async with async_session_factory() as session:
        # 1. Create permissions (skip existing)
        perm_map: dict[str, str] = {}  # code → id

        for perm_def in DEFAULT_PERMISSIONS:
            existing = await session.execute(
                select(PermissionModel).where(PermissionModel.code == perm_def["code"])
            )
            perm = existing.scalar_one_or_none()

            if perm:
                perm_map[perm.code] = str(perm.id)
                print(f"  [skip] Permission '{perm_def['code']}' already exists")
            else:
                new_perm = PermissionModel(
                    id=uuid4(),
                    code=perm_def["code"],
                    name=perm_def["name"],
                    description="",
                    scope=perm_def["scope"],
                    resource=perm_def["resource"],
                    action=perm_def["action"],
                    is_active=True,
                    created_by="seed_script",
                    modified_by="seed_script",
                )
                session.add(new_perm)
                perm_map[perm_def["code"]] = str(new_perm.id)
                print(f"  [new]  Permission '{perm_def['code']}' created")

        await session.flush()

        # 2. Assign permissions to roles
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role_result = await session.execute(
                select(RoleModel).where(RoleModel.code == role_code)
            )
            role = role_result.scalar_one_or_none()
            if not role:
                print(f"  [warn] Role '{role_code}' not found — skipping assignments")
                continue

            for perm_code in perm_codes:
                perm_id = perm_map.get(perm_code)
                if not perm_id:
                    continue

                existing_rp = await session.execute(
                    select(RolePermissionModel).where(
                        RolePermissionModel.role_id == str(role.id),
                        RolePermissionModel.permission_id == perm_id,
                    )
                )
                if existing_rp.scalar_one_or_none():
                    continue

                rp = RolePermissionModel(
                    id=uuid4(),
                    role_id=str(role.id),
                    permission_id=perm_id,
                    created_by="seed_script",
                    modified_by="seed_script",
                )
                session.add(rp)
                print(f"  [link] {role_code} ← {perm_code}")

        await session.commit()
        print("\n✓ RBAC seed complete.")

    # 3. Assign ADMIN role to all existing users who don't have any role assignment
    async with async_session_factory() as session:
        print("\nAssigning default role to existing users without role assignments...")

        # Find the ADMIN role
        admin_role_result = await session.execute(
            select(RoleModel).where(RoleModel.code == "ADMIN")
        )
        admin_role = admin_role_result.scalar_one_or_none()
        if not admin_role:
            print("  [warn] ADMIN role not found — skipping user assignments")
        else:
            # Find all users
            users_result = await session.execute(select(UserModel))
            users = users_result.scalars().all()

            for user in users:
                # Check if user already has any role assignment
                existing_assignment = await session.execute(
                    select(RoleAssignmentModel).where(
                        RoleAssignmentModel.user_id == str(user.id),
                    )
                )
                if existing_assignment.scalar_one_or_none():
                    print(f"  [skip] User '{user.username}' already has a role assignment")
                    continue

                # Assign ADMIN role as default for existing users
                assignment = RoleAssignmentModel(
                    id=uuid4(),
                    user_id=str(user.id),
                    role_id=str(admin_role.id),
                    tenant_id=None,
                    is_active=True,
                    created_by="seed_script",
                    modified_by="seed_script",
                )
                session.add(assignment)
                print(f"  [new]  User '{user.username}' → Role 'ADMIN'")

        await session.commit()
        print("\n✓ Role assignments complete.")


if __name__ == "__main__":
    print("Seeding RBAC permissions...")
    asyncio.run(seed())

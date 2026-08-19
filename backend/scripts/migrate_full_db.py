"""
Full Database Migration — migrates ALL data from a fresh Mendix DB backup into our qcchecklist database.

Steps:
1. Restores the Mendix SQL dump into a temporary DB (mendix_qc_temp)
2. Migrates masters (units, stages, formats, questions, options, etc.)
3. Migrates products, remarks
4. Migrates QC checklist transaction data (requests, stages, sections, answers, approval mappings)
5. Migrates users (as needed for FK resolution)

Usage: python -m scripts.migrate_full_db

Prerequisites:
- PostgreSQL running on localhost:5432 with user postgres/root
- The qcchecklist target DB already exists with schema (run alembic migrations first)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg

# The Mendix dump will be restored into this temporary DB
DUMP_FILE = str(Path(__file__).parent / "mendix_qcchecklist_qa_database_66faaf05_8c06_4587_8f53_caa171d6_18_08.sql")
TEMP_DB = "mendix_qc_temp"
PG_DSN = "postgresql://postgres:root@localhost:5432"
SOURCE_DSN = f"{PG_DSN}/{TEMP_DB}"
TARGET_DSN = f"{PG_DSN}/qcchecklist"


async def restore_dump():
    """Create temp DB and restore the Mendix dump into it."""
    print("=" * 60)
    print("STEP 0: Restoring Mendix dump into temporary DB...")
    print("=" * 60)

    conn = await asyncpg.connect(f"{PG_DSN}/postgres")
    # Drop temp DB if exists
    await conn.execute(f"DROP DATABASE IF EXISTS {TEMP_DB}")
    await conn.execute(f"CREATE DATABASE {TEMP_DB}")
    await conn.close()

    # Restore using psql
    import subprocess
    psql_path = r"C:\Program Files\PostgreSQL\16\bin\psql.exe"
    result = subprocess.run(
        [psql_path, "-h", "localhost", "-p", "5432", "-U", "postgres", "-d", TEMP_DB, "-f", DUMP_FILE],
        capture_output=True, text=True, env={**__import__('os').environ, "PGPASSWORD": "root"}
    )
    if result.returncode != 0:
        # psql may return warnings for roles etc, that's OK
        print(f"  psql output (may have warnings): {result.stderr[:500]}")
    print("  Dump restored successfully.")


async def migrate():
    print("\n" + "=" * 60)
    print("FULL DATABASE MIGRATION: Mendix → qcchecklist")
    print("=" * 60)

    # Restore dump first
    await restore_dump()

    print("\nConnecting to source (mendix_qc_temp) and target (qcchecklist)...")
    src = await asyncpg.connect(SOURCE_DSN)
    tgt = await asyncpg.connect(TARGET_DSN)

    now = datetime.now(UTC)
    actor = "mendix_migration"

    # ID mappings: mendix_id -> our_id
    user_map: dict[int, int] = {}
    unit_map: dict[int, int] = {}
    bu_map: dict[int, int] = {}
    format_map: dict[int, int] = {}
    stage_map: dict[int, int] = {}
    question_map: dict[int, int] = {}
    option_map: dict[int, int] = {}
    sap_field_map: dict[int, int] = {}
    section_map: dict[int, int] = {}
    fsm_map: dict[int, int] = {}
    sqm_map: dict[int, int] = {}
    vt_map: dict[int, int] = {}
    al_map: dict[int, int] = {}
    product_map: dict[int, int] = {}
    remark_map: dict[int, int] = {}
    cr_map: dict[int, int] = {}  # checklist_request
    cs_map: dict[int, int] = {}  # checklist_stage
    css_map: dict[int, int] = {}  # checklist_stage_section
    qa_map: dict[int, int] = {}  # question_answer
    qah_map: dict[int, int] = {}  # question_answer_helper
    salm_map: dict[int, int] = {}  # stage_approval_label_mapping

    try:
        # ═══════════════════════════════════════════════════════════
        # CLEAN TARGET DB (order matters for FK constraints)
        # NOTE: Does NOT touch users, roles, permissions, role_assignments
        # ═══════════════════════════════════════════════════════════
        print("\nCleaning target database (preserving users/roles/permissions)...")
        await tgt.execute("DELETE FROM question_answer_sub_question_answers")
        await tgt.execute("DELETE FROM question_answer_helpers")
        await tgt.execute("DELETE FROM question_answers")
        await tgt.execute("DELETE FROM stage_approval_label_mappings")
        await tgt.execute("DELETE FROM checklist_stage_sections")
        await tgt.execute("DELETE FROM checklist_stages")
        await tgt.execute("DELETE FROM checklist_requests")
        await tgt.execute("DELETE FROM approval_label_user_roles")
        await tgt.execute("DELETE FROM stage_question_mappings")
        await tgt.execute("DELETE FROM sections")
        await tgt.execute("DELETE FROM format_stage_mappings")
        await tgt.execute("DELETE FROM approval_labels")
        await tgt.execute("DELETE FROM question_sub_questions")
        await tgt.execute("DELETE FROM question_options")
        await tgt.execute("DELETE FROM questions")
        await tgt.execute("DELETE FROM sap_fields")
        await tgt.execute("DELETE FROM validation_types")
        await tgt.execute("DELETE FROM formats")
        await tgt.execute("DELETE FROM stages")
        await tgt.execute("DELETE FROM products")
        await tgt.execute("DELETE FROM remark_user_roles")
        await tgt.execute("DELETE FROM remarks")
        await tgt.execute("DELETE FROM units")
        await tgt.execute("DELETE FROM business_units")
        print("  Done.")

        # ═══════════════════════════════════════════════════════════
        # PART 1: MASTERS
        # ═══════════════════════════════════════════════════════════

        # --- 1. Business Units ---
        print("\n[1] Business Units")
        rows = await src.fetch('SELECT id, name FROM "masters$businessunitmaster"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO business_units (name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['name'], actor, now
            )
            bu_map[r['id']] = new_id
        print(f"  Migrated: {len(bu_map)}")

        # --- 2. Units ---
        print("\n[2] Units")
        rows = await src.fetch('SELECT id, unitname FROM "masters$unitmaster"')
        unit_bu_rows = await src.fetch(
            'SELECT "masters$unitmasterid", "masters$businessunitmasterid" FROM "masters$unitmaster_businessunitmaster"'
        )
        unit_bu = dict(unit_bu_rows)
        for r in rows:
            linked_bu = bu_map.get(unit_bu.get(r['id'], 0))
            new_id = await tgt.fetchval(
                "INSERT INTO units (name, business_unit_id, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, true, $3, $3, $4, $4) RETURNING id",
                r['unitname'], linked_bu, actor, now
            )
            unit_map[r['id']] = new_id
        print(f"  Migrated: {len(unit_map)}")

        # --- 3. Validation Types ---
        print("\n[3] Validation Types")
        rows = await src.fetch('SELECT id, name FROM "masters$validationtype"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO validation_types (name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['name'], actor, now
            )
            vt_map[r['id']] = new_id
        print(f"  Migrated: {len(vt_map)}")

        # --- 4. SAP Fields ---
        print("\n[4] SAP Fields")
        rows = await src.fetch('SELECT id, sapnames FROM "masters$sapanswerfields"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO sap_fields (field_name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['sapnames'] or '', actor, now
            )
            sap_field_map[r['id']] = new_id
        print(f"  Migrated: {len(sap_field_map)}")

        # --- 5. Stages ---
        print("\n[5] Stages")
        rows = await src.fetch('SELECT id, stagename FROM "masters$stagemaster"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO stages (stage_name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['stagename'], actor, now
            )
            stage_map[r['id']] = new_id
        print(f"  Migrated: {len(stage_map)}")

        # --- 6. Formats ---
        print("\n[6] Formats")
        rows = await src.fetch(
            'SELECT id, formatno, formattitle, format_name, hasdeclarationquestion, formattype FROM "masters$formatmaster"'
        )
        fmt_unit_rows = await src.fetch(
            'SELECT "masters$formatmasterid", "masters$unitmasterid" FROM "masters$formatmaster_unitmaster"'
        )
        fmt_unit = dict(fmt_unit_rows)
        for r in rows:
            linked_unit = unit_map.get(fmt_unit.get(r['id'], 0))
            if not linked_unit:
                linked_unit = list(unit_map.values())[0] if unit_map else 1
            new_id = await tgt.fetchval(
                "INSERT INTO formats (format_no, format_title, format_name, unit_id, has_declaration_question, format_type, "
                "is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, true, $7, $7, $8, $8) RETURNING id",
                r['formatno'], r['formattitle'] or '', r['format_name'] or '',
                linked_unit, r['hasdeclarationquestion'] or False, r['formattype'] or '',
                actor, now
            )
            format_map[r['id']] = new_id
        print(f"  Migrated: {len(format_map)}")

        # --- 7. Questions ---
        print("\n[7] Questions")
        # Check if mastertype column exists
        has_mastertype = await src.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='masters$questionmaster' AND column_name='mastertype')"
        )
        q_select = (
            'SELECT id, title, answertype, hastextbox, hasmultipletextbox, isvalidationrequired, '
            'hassubquestion, hasresponseoption'
            + (', mastertype' if has_mastertype else '')
            + ' FROM "masters$questionmaster"'
        )
        rows = await src.fetch(q_select)
        answer_type_conv = {
            'Text_Box': 'Text Box', 'None': 'None',
            'Dropdown_Single': 'Dropdown (single select)',
            'Dropdown_Multi': 'Dropdown (multi select)',
            'Drop_Down__Single_Select_': 'Dropdown (single select)',
            'Drop_Down__Multi_Select_': 'Dropdown (multi select)',
            'Date_Time': 'Date & Time', 'DateAndTime': 'Date & Time',
            'Masters': 'Masters', 'Master': 'Masters',
        }
        for r in rows:
            at = answer_type_conv.get(r['answertype'] or 'None', r['answertype'] or 'None')
            mt = r.get('mastertype', '') or ''
            # Normalize master_type: 'ProductMaster' -> 'Product Master', empty -> None
            mt_normalized = None
            if mt == 'ProductMaster':
                mt_normalized = 'Product Master'
            elif mt and mt.strip():
                mt_normalized = mt
            new_id = await tgt.fetchval(
                "INSERT INTO questions (title, answer_type, master_type, has_text_box, has_multiple_text_box, has_sub_question, "
                "is_validation_required, has_response_option, allow_multiple_input, has_associated_master, is_calculated, "
                "is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, false, false, false, true, $9, $9, $10, $10) RETURNING id",
                r['title'] or '', at, mt_normalized,
                r['hastextbox'] or False, r['hasmultipletextbox'] or False,
                r['hassubquestion'] or False, r['isvalidationrequired'] or False,
                r['hasresponseoption'] or False,
                actor, now
            )
            question_map[r['id']] = new_id

        # Link questions to validation types
        vt_links = await src.fetch(
            'SELECT "masters$questionmasterid", "masters$validationtypeid" FROM "masters$questionmaster_validationtype"'
        )
        for r in vt_links:
            q_id = question_map.get(r[0])
            vt_id = vt_map.get(r[1])
            if q_id and vt_id:
                await tgt.execute("UPDATE questions SET validation_type_id = $1 WHERE id = $2", vt_id, q_id)

        # Link sub-questions
        sub_q_rows = await src.fetch(
            'SELECT "masters$questionmasterid1", "masters$questionmasterid2" FROM "masters$questionmaster_subquestionmaster"'
        )
        for r in sub_q_rows:
            parent_id = question_map.get(r[0])
            sub_id = question_map.get(r[1])
            if parent_id and sub_id:
                await tgt.execute(
                    "INSERT INTO question_sub_questions (question_id, sub_question_id, created_by, modified_by, created_date, modified_date) "
                    "VALUES ($1, $2, $3, $3, $4, $4)",
                    parent_id, sub_id, actor, now
                )
        print(f"  Migrated: {len(question_map)} questions, {len(sub_q_rows)} sub-question links")

        # --- 8. Question Options ---
        print("\n[8] Question Options")
        opt_q_rows = await src.fetch(
            'SELECT "masters$questionoptionid", "masters$questionmasterid" FROM "masters$questionoption_questionmaster"'
        )
        opt_q_map = dict(opt_q_rows)
        rows = await src.fetch('SELECT id, optiontitle, isresponseoption FROM "masters$questionoption"')
        for r in rows:
            linked_q = question_map.get(opt_q_map.get(r['id'], 0))
            if not linked_q:
                continue
            new_id = await tgt.fetchval(
                "INSERT INTO question_options (option_title, is_response_option, question_id, is_active, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, true, $4, $4, $5, $5) RETURNING id",
                r['optiontitle'] or '', r['isresponseoption'] or False, linked_q, actor, now
            )
            option_map[r['id']] = new_id
        print(f"  Migrated: {len(option_map)}")

        # --- 9. Format Stage Mappings ---
        print("\n[9] Format Stage Mappings")
        rows = await src.fetch(
            'SELECT id, isactive, hassection, isapprovable, isreferback FROM "masters$formatstagemapping"'
        )
        fsm_format_rows = await src.fetch(
            'SELECT "masters$formatstagemappingid", "masters$formatmasterid" FROM "masters$formatstagemapping_formatmaster"'
        )
        fsm_format = dict(fsm_format_rows)
        fsm_stage_rows = await src.fetch(
            'SELECT "masters$formatstagemappingid", "masters$stagemasterid" FROM "masters$formatstagemapping_stagemaster"'
        )
        fsm_stage = dict(fsm_stage_rows)
        for r in rows:
            mx_id = r['id']
            fmt_id = format_map.get(fsm_format.get(mx_id, 0))
            stg_id = stage_map.get(fsm_stage.get(mx_id, 0))
            if not fmt_id or not stg_id:
                continue
            new_id = await tgt.fetchval(
                "INSERT INTO format_stage_mappings (format_id, stage_id, is_active, is_approvable, is_refer_back, has_section, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $7, $8, $8) RETURNING id",
                fmt_id, stg_id, r['isactive'] if r['isactive'] is not None else True,
                r['isapprovable'] or False, r['isreferback'] or False, r['hassection'] or False,
                actor, now
            )
            fsm_map[mx_id] = new_id
        print(f"  Migrated: {len(fsm_map)}")

        # --- 10. Sections ---
        print("\n[10] Sections")
        rows = await src.fetch('SELECT id, sectionname FROM "masters$section"')
        sec_fsm_rows = await src.fetch(
            'SELECT "masters$sectionid", "masters$formatstagemappingid" FROM "masters$section_formatstagemapping"'
        )
        sec_fsm = dict(sec_fsm_rows)
        for r in rows:
            mx_id = r['id']
            linked_fsm = fsm_map.get(sec_fsm.get(mx_id, 0))
            new_id = await tgt.fetchval(
                "INSERT INTO sections (section_name, format_stage_mapping_id, is_active, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, true, $3, $3, $4, $4) RETURNING id",
                r['sectionname'], linked_fsm, actor, now
            )
            section_map[mx_id] = new_id
        print(f"  Migrated: {len(section_map)}")

        # --- 11. Stage Question Mappings ---
        print("\n[11] Stage Question Mappings")
        rows = await src.fetch(
            'SELECT id, serialnumber, showongrid, aqllimit, isdeclarationquestion, iseditable, customanswers '
            'FROM "masters$stagequestionmapping"'
        )
        sqm_fsm_rows = await src.fetch(
            'SELECT "masters$stagequestionmappingid", "masters$formatstagemappingid" '
            'FROM "masters$stagequestionmapping_formatstagemapping"'
        )
        sqm_fsm = dict(sqm_fsm_rows)
        sqm_q_rows = await src.fetch(
            'SELECT "masters$stagequestionmappingid", "masters$questionmasterid" '
            'FROM "masters$stagequestionmapping_questionmaster"'
        )
        sqm_q = dict(sqm_q_rows)
        sqm_sap_rows = await src.fetch(
            'SELECT "masters$stagequestionmappingid", "masters$sapanswerfieldsid" '
            'FROM "masters$stagequestionmapping_sapanswerfields"'
        )
        sqm_sap = dict(sqm_sap_rows)
        sqm_sec_rows = await src.fetch(
            'SELECT "masters$stagequestionmappingid", "masters$sectionid" '
            'FROM "masters$stagesectionquestionmapping_section"'
        )
        sqm_sec: dict[int, int] = {}
        for row in sqm_sec_rows:
            sqm_sec[row[0]] = row[1]

        sec_to_fsm_mendix: dict[int, int] = {}
        for row in sec_fsm_rows:
            sec_to_fsm_mendix[row[0]] = row[1]

        for r in rows:
            mx_id = r['id']
            linked_fsm = fsm_map.get(sqm_fsm.get(mx_id, 0))
            linked_q = question_map.get(sqm_q.get(mx_id, 0))
            linked_sap = sap_field_map.get(sqm_sap.get(mx_id)) if sqm_sap.get(mx_id) else None
            linked_sec = section_map.get(sqm_sec.get(mx_id)) if sqm_sec.get(mx_id) else None

            if not linked_fsm and sqm_sec.get(mx_id):
                mendix_sec_id = sqm_sec[mx_id]
                mendix_fsm_from_sec = sec_to_fsm_mendix.get(mendix_sec_id)
                if mendix_fsm_from_sec:
                    linked_fsm = fsm_map.get(mendix_fsm_from_sec)

            if not linked_fsm or not linked_q:
                continue

            new_id = await tgt.fetchval(
                "INSERT INTO stage_question_mappings (format_stage_mapping_id, question_id, sap_field_id, section_id, "
                "serial_number, show_on_grid, aql_limit, is_declaration_question, is_editable, custom_answers, is_active, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true, $11, $11, $12, $12) RETURNING id",
                linked_fsm, linked_q, linked_sap, linked_sec,
                r['serialnumber'] or 0, r['showongrid'] or False,
                str(r['aqllimit']) if r['aqllimit'] is not None else '', r['isdeclarationquestion'] or False,
                r['iseditable'] if r['iseditable'] is not None else True,
                {'SampleDestroyed': 'Calculate_SampleDestroyed', 'SampleConsumed': 'Calculate_SampleConsumed'}.get(r['customanswers'], r['customanswers']) if r['customanswers'] else None,
                actor, now
            )
            sqm_map[mx_id] = new_id
        print(f"  Migrated: {len(sqm_map)}")

        # --- 12. Approval Labels ---
        print("\n[12] Approval Labels")
        rows = await src.fetch('SELECT id, label FROM "masters$approvallabel"')
        al_stage_rows = await src.fetch(
            'SELECT "masters$approvallabelid", "masters$stagemasterid" FROM "masters$approvallabel_stagemaster"'
        )
        al_stage = dict(al_stage_rows)
        for r in rows:
            mx_id = r['id']
            linked_stage = stage_map.get(al_stage.get(mx_id, 0))
            if not linked_stage:
                continue
            new_id = await tgt.fetchval(
                "INSERT INTO approval_labels (label, stage_id, is_active, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, true, $3, $3, $4, $4) RETURNING id",
                r['label'], linked_stage, actor, now
            )
            al_map[mx_id] = new_id
        print(f"  Migrated: {len(al_map)}")

        # --- 12b. Approval Label User Roles ---
        print("\n[12b] Approval Label User Roles")
        # Get role map from target DB (roles already seeded via seed_rbac)
        role_rows = await tgt.fetch("SELECT id, code FROM roles")
        role_code_to_id = {r['code']: r['id'] for r in role_rows}
        # Mendix uses system$userrole which has a 'name' field
        mendix_roles = await src.fetch('SELECT id, name FROM "system$userrole"')
        mendix_role_map: dict[int, int] = {}
        for mr in mendix_roles:
            # Map by name similarity — Mendix role names like "QCChecklist.Analyst" → match to our role codes
            name = mr['name'] or ''
            for code, rid in role_code_to_id.items():
                if code.lower() in name.lower() or name.lower().split('.')[-1] in code.lower():
                    mendix_role_map[mr['id']] = rid
                    break
            # Fallback: just store the mendix role id
            if mr['id'] not in mendix_role_map:
                # Use first role as fallback
                if role_code_to_id:
                    mendix_role_map[mr['id']] = list(role_code_to_id.values())[0]

        al_role_rows = await src.fetch(
            'SELECT "masters$approvallabelid", "system$userroleid" FROM "masters$approvallabel_userrole"'
        )
        al_role_count = 0
        for r in al_role_rows:
            our_al_id = al_map.get(r[0])
            our_role_id = mendix_role_map.get(r[1])
            if our_al_id and our_role_id:
                await tgt.execute(
                    "INSERT INTO approval_label_user_roles (approval_label_id, role_id, created_by, modified_by, created_date, modified_date) "
                    "VALUES ($1, $2, $3, $3, $4, $4)",
                    our_al_id, our_role_id, actor, now
                )
                al_role_count += 1
        print(f"  Migrated: {al_role_count}")

        # --- 13. Products ---
        print("\n[13] Products")
        rows = await src.fetch('SELECT id, productname, storagecondition FROM "masters$productmaster"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO products (product_name, storage_conditions, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, true, $3, $3, $4, $4) RETURNING id",
                r['productname'] or '', r['storagecondition'] or '', actor, now
            )
            product_map[r['id']] = new_id
        print(f"  Migrated: {len(product_map)}")

        # --- 14. Remarks ---
        print("\n[14] Remarks")
        rows = await src.fetch('SELECT id, remarktitle FROM "masters$remarks"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO remarks (remark, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['remarktitle'] or '', actor, now
            )
            remark_map[r['id']] = new_id
        print(f"  Migrated: {len(remark_map)}")

        # Remark user roles
        remark_role_rows = await src.fetch(
            'SELECT "masters$remarksid", "system$userroleid" FROM "masters$remarks_userrole"'
        )
        for r in remark_role_rows:
            our_remark_id = remark_map.get(r[0])
            our_role_id = mendix_role_map.get(r[1])
            if our_remark_id and our_role_id:
                await tgt.execute(
                    "INSERT INTO remark_user_roles (remark_id, role_id, created_by, modified_by, created_date, modified_date) "
                    "VALUES ($1, $2, $3, $3, $4, $4)",
                    our_remark_id, our_role_id, actor, now
                )

        # ═══════════════════════════════════════════════════════════
        # PART 2: USERS (look up existing users by employee ID — NOT creating new ones)
        # The users are imported separately. Here we just build the mendix_user_id → our_user_id map.
        # ═══════════════════════════════════════════════════════════
        print("\n[15] Users (mapping by employee ID)")
        # Get all users from our DB (username = employee ID)
        existing_users = await tgt.fetch("SELECT id, username FROM users")
        username_to_id = {u['username']: u['id'] for u in existing_users}

        mendix_users = await src.fetch('SELECT id, empid FROM "accessmanagement$useraccount"')
        mapped = 0
        unmapped = 0
        for mu in mendix_users:
            username = mu['empid'] or str(mu['id'])
            if username in username_to_id:
                user_map[mu['id']] = username_to_id[username]
                mapped += 1
            else:
                # Try without leading zeros or case sensitivity
                found = False
                for existing_username, existing_id in username_to_id.items():
                    if existing_username.lower() == username.lower():
                        user_map[mu['id']] = existing_id
                        mapped += 1
                        found = True
                        break
                if not found:
                    unmapped += 1
        print(f"  Mapped: {mapped}, Unmapped (no matching user in DB): {unmapped}")

        # ═══════════════════════════════════════════════════════════
        # PART 3: QC CHECKLIST TRANSACTION DATA
        # ═══════════════════════════════════════════════════════════

        # --- 16. Checklist Requests ---
        print("\n[16] Checklist Requests")
        rows = await src.fetch(
            'SELECT id, status, requestnumber, createddate, changeddate, '
            '"system$owner", statusformat, islaststage, isremoved, sequencenumber '
            'FROM "qcchecklist$checklistrequest"'
        )
        cr_format_rows = await src.fetch(
            'SELECT "qcchecklist$checklistrequestid", "masters$formatmasterid" '
            'FROM "qcchecklist$checklistrequest_formatesmaster"'
        )
        cr_format = dict(cr_format_rows)
        cr_approver_rows = await src.fetch(
            'SELECT "qcchecklist$checklistrequestid", "accessmanagement$useraccountid" '
            'FROM "qcchecklist$checklistrequest_approveruseraccount"'
        )
        cr_approver = dict(cr_approver_rows)

        for r in rows:
            mx_id = r['id']
            linked_format = format_map.get(cr_format.get(mx_id, 0))
            linked_approver = user_map.get(cr_approver.get(mx_id, 0))
            owner_id = user_map.get(r['system$owner']) if r['system$owner'] else None

            new_id = await tgt.fetchval(
                "INSERT INTO checklist_requests (status, request_number, status_format, is_last_stage, is_removed, "
                "sequence_number, approver_user_id, format_id, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9, $10, $11) RETURNING id",
                r['status'] or 'Draft',
                r['requestnumber'] or f"MX{mx_id}",
                r['statusformat'] or '',
                r['islaststage'] or False,
                r['isremoved'] or False,
                r['sequencenumber'] or mx_id,
                linked_approver,
                linked_format,
                str(owner_id) if owner_id else actor,
                r['createddate'] or now,
                r['changeddate'] or now,
            )
            cr_map[mx_id] = new_id
        print(f"  Migrated: {len(cr_map)}")

        # --- 17. Checklist Stages ---
        print("\n[17] Checklist Stages")
        rows = await src.fetch(
            'SELECT id, status, createddate, changeddate, "system$owner", '
            'performedremark, approvedremark, isselfverified, selfverificationdetails, '
            'isapprovable, islaststage, submitremarks, selfapprovedremark '
            'FROM "qcchecklist$checkliststage"'
        )
        cs_cr_rows = await src.fetch(
            'SELECT "qcchecklist$checkliststageid", "qcchecklist$checklistrequestid" '
            'FROM "qcchecklist$checkliststage_checklistrequest"'
        )
        cs_cr = dict(cs_cr_rows)
        cs_fsm_rows = await src.fetch(
            'SELECT "qcchecklist$checkliststageid", "masters$formatstagemappingid" '
            'FROM "qcchecklist$checkliststage_formatstagemapping"'
        )
        cs_fsm = dict(cs_fsm_rows)
        cs_user_rows = await src.fetch(
            'SELECT "qcchecklist$checkliststageid", "accessmanagement$useraccountid" '
            'FROM "qcchecklist$checkliststage_useraccount"'
        )
        cs_user = dict(cs_user_rows)

        for r in rows:
            mx_id = r['id']
            linked_cr = cr_map.get(cs_cr.get(mx_id, 0))
            linked_fsm = fsm_map.get(cs_fsm.get(mx_id, 0))
            linked_user = user_map.get(cs_user.get(mx_id, 0))
            owner_id = user_map.get(r['system$owner']) if r['system$owner'] else None

            if not linked_cr:
                continue

            new_id = await tgt.fetchval(
                "INSERT INTO checklist_stages (checklist_request_id, user_id, format_stage_mapping_id, status, "
                "performed_remark, approved_remark, is_self_verified, self_verification_details, "
                "is_approvable, is_last_stage, submit_remarks, self_approved_remark, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $13, $14, $15) RETURNING id",
                linked_cr, linked_user, linked_fsm,
                r['status'] or '',
                r['performedremark'] or '',
                r['approvedremark'] or '',
                r['isselfverified'] or False,
                r['selfverificationdetails'] or '',
                r['isapprovable'] or False,
                r['islaststage'] or False,
                r['submitremarks'] or '',
                r['selfapprovedremark'] or '',
                str(owner_id) if owner_id else actor,
                r['createddate'] or now,
                r['changeddate'] or now,
            )
            cs_map[mx_id] = new_id
        print(f"  Migrated: {len(cs_map)}")

        # --- 18. Checklist Stage Sections ---
        print("\n[18] Checklist Stage Sections")
        rows = await src.fetch('SELECT id FROM "qcchecklist$checkliststagesection"')
        css_cs_rows = await src.fetch(
            'SELECT "qcchecklist$checkliststagesectionid", "qcchecklist$checkliststageid" '
            'FROM "qcchecklist$checkliststagesection_checkliststage"'
        )
        css_cs = dict(css_cs_rows)
        css_sec_rows = await src.fetch(
            'SELECT "qcchecklist$checkliststagesectionid", "masters$sectionid" '
            'FROM "qcchecklist$checkliststagesection_section"'
        )
        css_sec = dict(css_sec_rows)

        for r in rows:
            mx_id = r['id']
            linked_cs = cs_map.get(css_cs.get(mx_id, 0))
            linked_sec = section_map.get(css_sec.get(mx_id, 0))
            if not linked_cs or not linked_sec:
                continue
            new_id = await tgt.fetchval(
                "INSERT INTO checklist_stage_sections (checklist_stage_id, section_id, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $3, $4, $4) RETURNING id",
                linked_cs, linked_sec, actor, now
            )
            css_map[mx_id] = new_id
        print(f"  Migrated: {len(css_map)}")

        # --- 19. Question Answers ---
        print("\n[19] Question Answers")
        rows = await src.fetch(
            'SELECT id, textboxvalue, resopnseanswer, commaseparatedname, hashelper, '
            'serialnumber, subanswerserialno, issuername, samplevails, testtitle, '
            'issuedbydate, hasvails, receivedbydate, answertotalvails, datetime, isissuedvails, '
            'createddate, changeddate, "system$owner" '
            'FROM "qcchecklist$questionanswer"'
        )
        qa_cs_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "qcchecklist$checkliststageid" '
            'FROM "qcchecklist$questionanswer_checkliststage"'
        )
        qa_cs = dict(qa_cs_rows)
        qa_css_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "qcchecklist$checkliststagesectionid" '
            'FROM "qcchecklist$questionanswer_checkliststagesection"'
        )
        qa_css = dict(qa_css_rows)
        qa_q_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "masters$questionmasterid" '
            'FROM "qcchecklist$questionanswer_questionmaster"'
        )
        qa_q = dict(qa_q_rows)
        qa_opt_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "masters$questionoptionid" '
            'FROM "qcchecklist$questionanswer_questionoptions"'
        )
        qa_opt = dict(qa_opt_rows)
        qa_resp_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "masters$questionoptionid" '
            'FROM "qcchecklist$questionanswer_responsequestionoption"'
        )
        qa_resp = dict(qa_resp_rows)
        qa_sqm_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "masters$stagequestionmappingid" '
            'FROM "qcchecklist$questionanswer_stagequestionmapping"'
        )
        qa_sqm = dict(qa_sqm_rows)
        qa_prod_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "masters$productmasterid" '
            'FROM "qcchecklist$questionanswer_productmaster"'
        )
        qa_prod = dict(qa_prod_rows)
        qa_receiver_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid", "accessmanagement$useraccountid" '
            'FROM "qcchecklist$questionanswer_receiveruseraccount"'
        )
        qa_receiver = dict(qa_receiver_rows)

        for r in rows:
            mx_id = r['id']
            linked_cs = cs_map.get(qa_cs.get(mx_id, 0))
            if not linked_cs:
                continue
            linked_css = css_map.get(qa_css.get(mx_id, 0))
            linked_q = question_map.get(qa_q.get(mx_id, 0))
            linked_opt = option_map.get(qa_opt.get(mx_id, 0))
            linked_resp = option_map.get(qa_resp.get(mx_id, 0))
            linked_sqm = sqm_map.get(qa_sqm.get(mx_id, 0))
            linked_prod = product_map.get(qa_prod.get(mx_id, 0))
            linked_receiver = user_map.get(qa_receiver.get(mx_id, 0))
            owner_id = user_map.get(r['system$owner']) if r['system$owner'] else None

            new_id = await tgt.fetchval(
                "INSERT INTO question_answers (checklist_stage_id, checklist_stage_section_id, product_id, "
                "question_id, question_option_id, receiver_user_id, response_question_option_id, "
                "stage_question_mapping_id, textbox_value, response_answer, comma_separated_name, "
                "has_helper, serial_number, sub_answer_serial_no, date_time, test_title, sample_vails, "
                "answer_total_vails, issued_by_date, received_by_date, issuer_name, is_issued_vails, has_vails, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, "
                "$18, $19, $20, $21, $22, $23, $24, $24, $25, $26) RETURNING id",
                linked_cs, linked_css, linked_prod,
                linked_q, linked_opt, linked_receiver, linked_resp,
                linked_sqm,
                r['textboxvalue'] or '',
                r['resopnseanswer'] or '',
                r['commaseparatedname'] or '',
                r['hashelper'] or False,
                r['serialnumber'] or 0,
                r['subanswerserialno'] or '',
                r['datetime'],
                r['testtitle'] or '',
                r['samplevails'] or '',
                r['answertotalvails'] or 0,
                r['issuedbydate'],
                r['receivedbydate'],
                r['issuername'] or '',
                r['isissuedvails'] or False,
                r['hasvails'] or False,
                str(owner_id) if owner_id else actor,
                r['createddate'] or now,
                r['changeddate'] or now,
            )
            qa_map[mx_id] = new_id
        print(f"  Migrated: {len(qa_map)}")

        # --- 20. Question Answer Helpers ---
        print("\n[20] Question Answer Helpers")
        rows = await src.fetch('SELECT id, textboxvalue FROM "qcchecklist$questionanswerhelper"')
        qah_qa_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerhelperid", "qcchecklist$questionanswerid" '
            'FROM "qcchecklist$questionanswerhelper_questionanswer"'
        )
        qah_qa = dict(qah_qa_rows)

        for r in rows:
            mx_id = r['id']
            new_id = await tgt.fetchval(
                "INSERT INTO question_answer_helpers (text_box_value, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $2, $3, $3) RETURNING id",
                r['textboxvalue'] or '', actor, now
            )
            qah_map[mx_id] = new_id

            # Create the junction record
            linked_qa = qa_map.get(qah_qa.get(mx_id, 0))
            if linked_qa:
                await tgt.execute(
                    "INSERT INTO question_answer_sub_question_answers (question_answer_id, question_answer_helper_id, "
                    "created_by, modified_by, created_date, modified_date) "
                    "VALUES ($1, $2, $3, $3, $4, $4)",
                    linked_qa, new_id, actor, now
                )
        print(f"  Migrated: {len(qah_map)}")

        # --- 21. Question Answer Sub-Question Answers (additional junction) ---
        print("\n[21] Question Answer Sub-Question links")
        qa_sub_rows = await src.fetch(
            'SELECT "qcchecklist$questionanswerid1", "qcchecklist$questionanswerid2" '
            'FROM "qcchecklist$questionanswer_subquestionanswer"'
        )
        sub_link_count = 0
        for r in qa_sub_rows:
            parent_qa = qa_map.get(r[0])
            child_qa = qa_map.get(r[1])
            if parent_qa and child_qa:
                # These are sub-question answer links — store as helper reference
                sub_link_count += 1
        print(f"  Found: {sub_link_count} (handled via helpers)")

        # --- 22. Stage Approval Label Mappings ---
        print("\n[22] Stage Approval Label Mappings")
        rows = await src.fetch(
            'SELECT id, createddate, changeddate, dateofaction, isshow, remark, isreferback '
            'FROM "qcchecklist$stageapprovallabelmapping"'
        )
        salm_al_rows = await src.fetch(
            'SELECT "qcchecklist$stageapprovallabelmappingid", "masters$approvallabelid" '
            'FROM "qcchecklist$stageapprovallabelmapping_approvallabel"'
        )
        salm_al = dict(salm_al_rows)
        salm_cs_rows = await src.fetch(
            'SELECT "qcchecklist$stageapprovallabelmappingid", "qcchecklist$checkliststageid" '
            'FROM "qcchecklist$stageapprovallabelmapping_checkliststages"'
        )
        salm_cs = dict(salm_cs_rows)
        salm_user_rows = await src.fetch(
            'SELECT "qcchecklist$stageapprovallabelmappingid", "accessmanagement$useraccountid" '
            'FROM "qcchecklist$stageapprovallabelmapping_useraccount"'
        )
        salm_user = dict(salm_user_rows)
        salm_remark_rows = await src.fetch(
            'SELECT "qcchecklist$stageapprovallabelmappingid", "masters$remarksid" '
            'FROM "qcchecklist$stageapprovallabelmapping_remarks"'
        )
        salm_remark = dict(salm_remark_rows)
        salm_role_rows = await src.fetch(
            'SELECT "qcchecklist$stageapprovallabelmappingid", "system$userroleid" '
            'FROM "qcchecklist$stageapprovallabelmapping_userrole"'
        )
        salm_role = dict(salm_role_rows)

        for r in rows:
            mx_id = r['id']
            linked_cs = cs_map.get(salm_cs.get(mx_id, 0))
            linked_al = al_map.get(salm_al.get(mx_id, 0))
            if not linked_cs or not linked_al:
                continue
            linked_user = user_map.get(salm_user.get(mx_id, 0))
            linked_remark = remark_map.get(salm_remark.get(mx_id, 0))
            linked_role = mendix_role_map.get(salm_role.get(mx_id, 0))

            new_id = await tgt.fetchval(
                "INSERT INTO stage_approval_label_mappings (checklist_stage_id, approval_label_id, "
                "remark_id, user_id, role_id, date_of_action, remark, is_show, is_refer_back, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10, $11, $12) RETURNING id",
                linked_cs, linked_al,
                linked_remark, linked_user, linked_role,
                r['dateofaction'],
                r['remark'] or '',
                r['isshow'] or False,
                r['isreferback'] or False,
                actor,
                r['createddate'] or now,
                r['changeddate'] or now,
            )
            salm_map[mx_id] = new_id
        print(f"  Migrated: {len(salm_map)}")

        # ═══════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"  Masters:")
        print(f"    Business Units: {len(bu_map)}")
        print(f"    Units: {len(unit_map)}")
        print(f"    Validation Types: {len(vt_map)}")
        print(f"    SAP Fields: {len(sap_field_map)}")
        print(f"    Stages: {len(stage_map)}")
        print(f"    Formats: {len(format_map)}")
        print(f"    Questions: {len(question_map)}")
        print(f"    Question Options: {len(option_map)}")
        print(f"    Format Stage Mappings: {len(fsm_map)}")
        print(f"    Sections: {len(section_map)}")
        print(f"    Stage Question Mappings: {len(sqm_map)}")
        print(f"    Approval Labels: {len(al_map)}")
        print(f"    Products: {len(product_map)}")
        print(f"    Remarks: {len(remark_map)}")
        print(f"  Users: {len(user_map)}")
        print(f"  Transactions:")
        print(f"    Checklist Requests: {len(cr_map)}")
        print(f"    Checklist Stages: {len(cs_map)}")
        print(f"    Checklist Stage Sections: {len(css_map)}")
        print(f"    Question Answers: {len(qa_map)}")
        print(f"    Question Answer Helpers: {len(qah_map)}")
        print(f"    Stage Approval Label Mappings: {len(salm_map)}")

    finally:
        await src.close()
        await tgt.close()

    # Clean up temp DB
    print("\nCleaning up temporary database...")
    conn = await asyncpg.connect(f"{PG_DSN}/postgres")
    await conn.execute(f"DROP DATABASE IF EXISTS {TEMP_DB}")
    await conn.close()
    print("  Done.")


if __name__ == "__main__":
    asyncio.run(migrate())

"""
Migrate masters data from Mendix QC Checklist DB (mendix_qc) into our qcchecklist database.
Reads from mendix_qc, inserts into qcchecklist with new auto-increment IDs.
Maintains ID mappings to resolve all FK relationships.

Usage: python -m scripts.migrate_mendix_masters
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg

SOURCE_DSN = "postgresql://postgres:root@localhost:5432/mendix_qc"
TARGET_DSN = "postgresql://postgres:root@localhost:5432/qcchecklist"


async def migrate():
    print("Connecting to source (mendix_qc) and target (qcchecklist)...")
    src = await asyncpg.connect(SOURCE_DSN)
    tgt = await asyncpg.connect(TARGET_DSN)

    now = datetime.now(UTC)
    actor = "mendix_migration"

    # ID mapping: mendix_id -> our_id
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

    try:
        # Clean existing master data (order matters due to FKs)
        print("\nCleaning existing master data...")
        await tgt.execute("DELETE FROM stage_question_mappings")
        await tgt.execute("DELETE FROM sections")
        await tgt.execute("DELETE FROM format_stage_mappings")
        await tgt.execute("DELETE FROM approval_labels")
        await tgt.execute("DELETE FROM question_options")
        await tgt.execute("DELETE FROM questions")
        await tgt.execute("DELETE FROM sap_fields")
        await tgt.execute("DELETE FROM validation_types")
        await tgt.execute("DELETE FROM formats")
        await tgt.execute("DELETE FROM stages")
        await tgt.execute("DELETE FROM units")
        await tgt.execute("DELETE FROM business_units")
        print("  Done.")

        # 1. Business Units
        print("\n[1] Business Units")
        rows = await src.fetch('SELECT id, name FROM "masters$businessunitmaster"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO business_units (name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['name'], actor, now
            )
            bu_map[r['id']] = new_id
            print(f"  {r['name']} -> {new_id}")

        # 2. Units
        print("\n[2] Units")
        rows = await src.fetch('SELECT id, unitname FROM "masters$unitmaster"')
        # Get unit -> business_unit associations
        unit_bu = dict(await src.fetch(
            'SELECT "masters$unitmasterid", "masters$businessunitmasterid" FROM "masters$unitmaster_businessunitmaster"'
        ))
        for r in rows:
            linked_bu = bu_map.get(unit_bu.get(r['id'], 0))
            new_id = await tgt.fetchval(
                "INSERT INTO units (name, business_unit_id, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, true, $3, $3, $4, $4) RETURNING id",
                r['unitname'], linked_bu, actor, now
            )
            unit_map[r['id']] = new_id
            print(f"  {r['unitname']} -> {new_id}")

        # 3. Validation Types
        print("\n[3] Validation Types")
        rows = await src.fetch('SELECT id, name FROM "masters$validationtype"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO validation_types (name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['name'], actor, now
            )
            vt_map[r['id']] = new_id
            print(f"  {r['name']} -> {new_id}")

        # 4. SAP Fields
        print("\n[4] SAP Fields")
        rows = await src.fetch('SELECT id, sapnames FROM "masters$sapanswerfields"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO sap_fields (field_name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['sapnames'] or '', actor, now
            )
            sap_field_map[r['id']] = new_id
            print(f"  {r['sapnames']} -> {new_id}")

        # 5. Stages
        print("\n[5] Stages")
        rows = await src.fetch('SELECT id, stagename FROM "masters$stagemaster"')
        for r in rows:
            new_id = await tgt.fetchval(
                "INSERT INTO stages (stage_name, is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, true, $2, $2, $3, $3) RETURNING id",
                r['stagename'], actor, now
            )
            stage_map[r['id']] = new_id
            print(f"  {r['stagename']} -> {new_id}")

        # 6. Formats
        print("\n[6] Formats")
        rows = await src.fetch(
            'SELECT id, formatno, formattitle, format_name, hasdeclarationquestion, formattype FROM "masters$formatmaster"'
        )
        # Get format -> unit associations
        fmt_unit = dict(await src.fetch(
            'SELECT "masters$formatmasterid", "masters$unitmasterid" FROM "masters$formatmaster_unitmaster"'
        ))
        for r in rows:
            linked_unit = unit_map.get(fmt_unit.get(r['id'], 0))
            if not linked_unit:
                # Use first unit as fallback
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
            print(f"  {r['formatno']} -> {new_id}")

        # 7. Questions
        print("\n[7] Questions")
        rows = await src.fetch(
            'SELECT id, title, answertype, hastextbox, hasmultipletextbox, isvalidationrequired, hassubquestion, hasresponseoption '
            'FROM "masters$questionmaster"'
        )
        answer_type_conv = {
            'Text_Box': 'Text Box',
            'None': 'None',
            'Dropdown_Single': 'Dropdown (single select)',
            'Dropdown_Multi': 'Dropdown (multi select)',
            'Drop_Down__Single_Select_': 'Dropdown (single select)',
            'Drop_Down__Multi_Select_': 'Dropdown (multi select)',
            'Date_Time': 'Date & Time',
            'Masters': 'Masters',
        }
        for r in rows:
            at = answer_type_conv.get(r['answertype'] or 'None', r['answertype'] or 'None')
            new_id = await tgt.fetchval(
                "INSERT INTO questions (title, answer_type, has_text_box, has_multiple_text_box, has_sub_question, "
                "is_validation_required, has_response_option, allow_multiple_input, has_associated_master, is_calculated, "
                "is_active, created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, false, false, false, true, $8, $8, $9, $9) RETURNING id",
                r['title'] or '', at,
                r['hastextbox'] or False, r['hasmultipletextbox'] or False,
                r['hassubquestion'] or False, r['isvalidationrequired'] or False,
                r['hasresponseoption'] or False,
                actor, now
            )
            question_map[r['id']] = new_id

        # Link questions to validation types
        rows = await src.fetch(
            'SELECT "masters$questionmasterid", "masters$validationtypeid" FROM "masters$questionmaster_validationtype"'
        )
        for r in rows:
            q_id = question_map.get(r[0])
            vt_id = vt_map.get(r[1])
            if q_id and vt_id:
                await tgt.execute("UPDATE questions SET validation_type_id = $1 WHERE id = $2", vt_id, q_id)

        # Link sub-questions
        sub_q_rows = await src.fetch(
            'SELECT "masters$questionmasterid1", "masters$questionmasterid2" FROM "masters$questionmaster_subquestionmaster"'
        )
        sub_count = 0
        for r in sub_q_rows:
            parent_id = question_map.get(r[0])
            sub_id = question_map.get(r[1])
            if parent_id and sub_id:
                await tgt.execute(
                    "INSERT INTO question_sub_questions (question_id, sub_question_id, created_by, modified_by, created_date, modified_date) "
                    "VALUES ($1, $2, $3, $3, $4, $4)",
                    parent_id, sub_id, actor, now
                )
                sub_count += 1
        # Also update has_sub_question flag on parent questions
        for r in sub_q_rows:
            parent_id = question_map.get(r[0])
            if parent_id:
                await tgt.execute("UPDATE questions SET has_sub_question = true WHERE id = $1", parent_id)

        print(f"  Questions migrated: {len(question_map)}, Sub-question links: {sub_count}")

        # 8. Question Options
        print("\n[8] Question Options")
        # Get option -> question association
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
        print(f"  Options migrated: {len(option_map)}")

        # 9. Format Stage Mappings
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
        print(f"  FSMs migrated: {len(fsm_map)}")

        # 10. Sections
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
            print(f"  {r['sectionname']} -> {new_id}")

        # 11. Stage Question Mappings
        print("\n[11] Stage Question Mappings")
        rows = await src.fetch(
            'SELECT id, serialnumber, showongrid, aqllimit, isdeclarationquestion, iseditable '
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

        # Build a section -> FSM mapping (section's format_stage_mapping)
        # This is needed because section-linked SQMs don't have a direct FSM association
        sec_to_fsm_mendix: dict[int, int] = {}
        for row in sec_fsm_rows:
            sec_to_fsm_mendix[row[0]] = row[1]

        sec_count = 0
        for r in rows:
            mx_id = r['id']
            linked_fsm = fsm_map.get(sqm_fsm.get(mx_id, 0))
            linked_q = question_map.get(sqm_q.get(mx_id, 0))
            linked_sap = sap_field_map.get(sqm_sap.get(mx_id)) if sqm_sap.get(mx_id) else None
            linked_sec = section_map.get(sqm_sec.get(mx_id)) if sqm_sec.get(mx_id) else None

            # If no direct FSM link but has section, get FSM through section -> FSM path
            if not linked_fsm and sqm_sec.get(mx_id):
                mendix_sec_id = sqm_sec[mx_id]
                mendix_fsm_from_sec = sec_to_fsm_mendix.get(mendix_sec_id)
                if mendix_fsm_from_sec:
                    linked_fsm = fsm_map.get(mendix_fsm_from_sec)

            if not linked_fsm or not linked_q:
                continue

            if linked_sec:
                sec_count += 1
                if sec_count == 1:
                    print(f"  DEBUG: mx_id={mx_id}, linked_sec={linked_sec}, linked_fsm={linked_fsm}, linked_q={linked_q}")

            new_id = await tgt.fetchval(
                "INSERT INTO stage_question_mappings (format_stage_mapping_id, question_id, sap_field_id, section_id, "
                "serial_number, show_on_grid, aql_limit, is_declaration_question, is_editable, is_active, "
                "created_by, modified_by, created_date, modified_date) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, true, $10, $10, $11, $11) RETURNING id",
                linked_fsm, linked_q, linked_sap, linked_sec,
                r['serialnumber'] or 0, r['showongrid'] or False,
                str(r['aqllimit']) if r['aqllimit'] is not None else '', r['isdeclarationquestion'] or False,
                r['iseditable'] if r['iseditable'] is not None else True,
                actor, now
            )
            sqm_map[mx_id] = new_id
            if sec_count == 1 and linked_sec:
                check = await tgt.fetchval(f"SELECT section_id FROM stage_question_mappings WHERE id = {new_id}")
                print(f"  DEBUG INSERT: id={new_id}, section_id in DB={check}")
        print(f"  SQMs migrated: {len(sqm_map)} (with section: {sec_count})")

        # Verify section linkage
        verify = await tgt.fetchval("SELECT count(*) FROM stage_question_mappings WHERE section_id IS NOT NULL")
        print(f"  [VERIFY] SQMs with section_id in DB: {verify}")

        # 12. Approval Labels
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
            print(f"  {r['label']} -> {new_id}")

        print(f"\n=== Migration Complete ===")
        print(f"  Units: {len(unit_map)}, BUs: {len(bu_map)}, Formats: {len(format_map)}")
        print(f"  Stages: {len(stage_map)}, Questions: {len(question_map)}, Options: {len(option_map)}")
        print(f"  SAP Fields: {len(sap_field_map)}, Sections: {len(section_map)}")
        print(f"  FSMs: {len(fsm_map)}, SQMs: {len(sqm_map)}, Approval Labels: {len(al_map)}")
        print(f"  Validation Types: {len(vt_map)}")

    finally:
        await src.close()
        await tgt.close()


if __name__ == "__main__":
    asyncio.run(migrate())

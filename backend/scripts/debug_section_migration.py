"""Debug script to check section migration issue."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import asyncpg

async def check():
    src = await asyncpg.connect("postgresql://postgres:root@localhost:5432/mendix_qc")
    tgt = await asyncpg.connect("postgresql://postgres:root@localhost:5432/qcchecklist")

    # Check sqm_sec mapping
    sqm_sec_rows = await src.fetch(
        'SELECT "masters$stagequestionmappingid", "masters$sectionid" '
        'FROM "masters$stagesectionquestionmapping_section"'
    )
    print(f"Total section-question links in Mendix: {len(sqm_sec_rows)}")
    sqm_sec = {}
    for row in sqm_sec_rows:
        sqm_sec[row[0]] = row[1]
    print(f"Unique SQM->Section entries: {len(sqm_sec)}")
    print(f"Sample keys (first 3): {list(sqm_sec.keys())[:3]}")
    print(f"Sample values (first 3): {list(sqm_sec.values())[:3]}")

    # Check what SQM IDs exist in mendix
    sqm_rows = await src.fetch('SELECT id FROM "masters$stagequestionmapping" LIMIT 5')
    print(f"\nSample SQM IDs from mendix: {[r['id'] for r in sqm_rows]}")

    # Check if the sqm_sec keys match sqm IDs
    sqm_all = await src.fetch('SELECT id FROM "masters$stagequestionmapping"')
    sqm_ids = {r['id'] for r in sqm_all}
    matched = sum(1 for k in sqm_sec if k in sqm_ids)
    print(f"SQM sec keys matching SQM table: {matched}/{len(sqm_sec)}")

    # Check target DB
    tgt_rows = await tgt.fetch("SELECT id, section_id FROM stage_question_mappings WHERE section_id IS NOT NULL LIMIT 5")
    print(f"\nTarget DB SQMs with section_id: {len(tgt_rows)}")

    await src.close()
    await tgt.close()

asyncio.run(check())

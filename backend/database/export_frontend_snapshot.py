# -*- coding: utf-8 -*-
"""
Xuất toàn bộ dữ liệu từ SQLite (dss_job_matching.db) ra:
1. backend/database/full_dataset_dump.json (phục vụ kiểm tra dữ liệu & minh họa báo cáo)
2. frontend/src/data/db_snapshot.js (phục vụ giao diện React & chế độ Instant Preview)
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.main import get_bootstrap_data, list_jobs_catalog

DUMP_JSON_PATH = ROOT_DIR / "backend" / "database" / "full_dataset_dump.json"
FRONTEND_DATA_PATH = ROOT_DIR / "frontend" / "src" / "data" / "db_snapshot.js"


def export_all():
    boot = get_bootstrap_data()
    all_jobs = list_jobs_catalog({})["jobs"]
    # Lấy toàn bộ 153 jobs không giới hạn 100
    from backend.services.dss_engine import get_db_connection, load_all_jobs_with_skills
    from backend.database.seed_data import DB_PATH

    conn = get_db_connection(DB_PATH)
    full_jobs = load_all_jobs_with_skills(conn)
    conn.close()

    full_bundle = {
        **boot,
        "jobs": full_jobs,
    }

    DUMP_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DUMP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(full_bundle, f, ensure_ascii=False, indent=2)

    FRONTEND_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    js_content = (
        "// Auto-generated from SQLite database (dss_job_matching.db)\n"
        "window.DSS_DB_SNAPSHOT = "
        + json.dumps(full_bundle, ensure_ascii=False)
        + ";\n"
    )
    with open(FRONTEND_DATA_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Exported {len(full_jobs)} jobs, {len(boot['skills'])} skills, {len(boot['student_profiles'])} profiles.")


if __name__ == "__main__":
    export_all()


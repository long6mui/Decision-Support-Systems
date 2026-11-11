# -*- coding: utf-8 -*-
"""
Backend Server cho Hệ Trợ Giúp Quyết Định (DSS): Trợ giúp Sinh viên Tốt nghiệp Tìm việc làm
Hỗ trợ song song:
1. FastAPI + Uvicorn (nếu môi trường đã cài đặt fastapi/uvicorn)
2. Built-in ThreadingHTTPServer (chạy trực tiếp bằng Python chuẩn + NumPy + SQLite mà không cần cài thêm thư viện ngoài)
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database.seed_data import DB_PATH, init_database
from backend.services.dss_engine import (
    AHP_PRESETS,
    calculate_ahp,
    get_db_connection,
    load_all_jobs_with_skills,
    run_dss_pipeline,
    run_what_if_simulation,
)


def ensure_db_ready():
    if not DB_PATH.exists():
        init_database(force_recreate=True)


def get_bootstrap_data() -> Dict[str, Any]:
    """Lấy toàn bộ dữ liệu danh mục khởi tạo cho Giao diện Trợ giúp Quyết định."""
    ensure_db_ready()
    conn = get_db_connection(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT * FROM majors ORDER BY id ASC")
    majors = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM skills ORDER BY id ASC")
    skills = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM companies ORDER BY rating DESC, id ASC")
    companies = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM criteria ORDER BY id ASC")
    criteria = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT sp.*, m.code AS major_code, m.name AS major_name, m.faculty
        FROM student_profiles sp
        JOIN majors m ON sp.major_id = m.id
        ORDER BY sp.id ASC
        """
    )
    students = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT ss.student_id, ss.skill_id, ss.proficiency_level, s.name AS skill_name, s.category
        FROM student_skills ss
        JOIN skills s ON ss.skill_id = s.id
        ORDER BY ss.proficiency_level DESC
        """
    )
    stu_skills_map: Dict[int, list] = {}
    for row in cur.fetchall():
        d = dict(row)
        stu_skills_map.setdefault(d["student_id"], []).append(d)

    for st in students:
        st["skills"] = stu_skills_map.get(st["id"], [])

    # Thống kê tổng quan kho dữ liệu việc làm
    cur.execute("SELECT COUNT(*) AS cnt, AVG(salary_min) AS avg_min, AVG(salary_max) AS avg_max FROM jobs")
    job_stat = dict(cur.fetchone())

    cur.execute(
        """
        SELECT m.code AS major_code, m.name AS major_name, COUNT(j.id) AS job_count,
               ROUND(AVG((j.salary_min + j.salary_max)/2.0), 1) AS avg_salary
        FROM majors m
        LEFT JOIN jobs j ON j.target_major_id = m.id
        GROUP BY m.id
        ORDER BY job_count DESC
        """
    )
    jobs_by_major = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "majors": majors,
        "skills": skills,
        "companies": companies,
        "criteria": criteria,
        "student_profiles": students,
        "ahp_presets": AHP_PRESETS,
        "market_stats": {
            "total_jobs": job_stat["cnt"],
            "total_companies": len(companies),
            "total_skills": len(skills),
            "total_majors": len(majors),
            "avg_salary_min": round(float(job_stat["avg_min"] or 0), 1),
            "avg_salary_max": round(float(job_stat["avg_max"] or 0), 1),
            "jobs_by_major": jobs_by_major,
        },
    }


def save_dss_session(result: Dict[str, Any]) -> int:
    """Lưu lại lịch sử phiên tư vấn quyết định vào bảng dss_sessions."""
    conn = get_db_connection(DB_PATH)
    cur = conn.cursor()
    student = result.get("student", {})
    ahp = result.get("ahp", {})
    top5_summary = [
        {
            "rank": j["topsis"]["rank"],
            "job_code": j["job_code"],
            "title": j["title"],
            "company": j["company_short"],
            "c_star": j["topsis"]["c_star"],
        }
        for j in result.get("ranked_jobs", [])[:5]
    ]
    cur.execute(
        """
        INSERT INTO dss_sessions (
            student_id, student_name, ahp_matrix_json, weights_json,
            lambda_max, consistency_index, consistency_ratio, top_results_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student.get("id"),
            student.get("full_name", "Sinh viên tùy chỉnh"),
            json.dumps(ahp.get("pairwise_matrix", [])),
            json.dumps(ahp.get("weights", [])),
            float(ahp.get("lambda_max", 6.0)),
            float(ahp.get("ci", 0.0)),
            float(ahp.get("cr", 0.0)),
            json.dumps(top5_summary, ensure_ascii=False),
        ),
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(session_id)


def list_jobs_catalog(query_params: Dict[str, list]) -> Dict[str, Any]:
    ensure_db_ready()
    conn = get_db_connection(DB_PATH)
    jobs = load_all_jobs_with_skills(conn)
    conn.close()

    major_code = (query_params.get("major_code") or [None])[0]
    level = (query_params.get("level") or [None])[0]
    q = ((query_params.get("q") or [""])[0]).strip().lower()

    filtered = []
    for j in jobs:
        if major_code and major_code != "ALL" and j["major_code"] != major_code:
            continue
        if level and level != "ALL" and j["level"] != level:
            continue
        if q and (q not in j["title"].lower() and q not in j["company_name"].lower()):
            continue
        filtered.append(j)

    return {
        "total": len(filtered),
        "jobs": filtered[:100],
    }


def get_recent_sessions() -> Dict[str, Any]:
    ensure_db_ready()
    conn = get_db_connection(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM dss_sessions ORDER BY id DESC LIMIT 15")
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["weights"] = json.loads(d["weights_json"])
        d["top_results"] = json.loads(d["top_results_json"])
        rows.append(d)
    conn.close()
    return {"sessions": rows}


class DSSRequestHandler(BaseHTTPRequestHandler):
    """Bộ xử lý HTTP RESTful API hỗ trợ CORS đầy đủ."""

    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        try:
            if path == "/api/health":
                self._send_json(200, {"status": "ok", "service": "HUST Job Matching DSS Engine"})
            elif path == "/api/bootstrap":
                self._send_json(200, get_bootstrap_data())
            elif path == "/api/jobs":
                self._send_json(200, list_jobs_catalog(query_params))
            elif path == "/api/sessions":
                self._send_json(200, get_recent_sessions())
            elif path in ("/", "/index.html") or path.startswith("/src/"):
                rel_path = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
                file_path = (ROOT_DIR / "frontend" / rel_path).resolve()
                frontend_root = (ROOT_DIR / "frontend").resolve()
                if str(file_path).startswith(str(frontend_root)) and file_path.is_file():
                    ext = file_path.suffix.lower()
                    mime_map = {
                        ".html": "text/html; charset=utf-8",
                        ".css": "text/css; charset=utf-8",
                        ".js": "application/javascript; charset=utf-8",
                        ".json": "application/json; charset=utf-8",
                    }
                    content_type = mime_map.get(ext, "application/octet-stream")
                    body = file_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self._send_json(404, {"error": f"Không tìm thấy tệp giao diện: {path}"})
            else:
                self._send_json(404, {"error": f"Endpoint không tồn tại: {path}"})
        except Exception as exc:
            traceback.print_exc()
            self._send_json(500, {"error": str(exc)})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"

        try:
            payload = json.loads(raw_body) if raw_body else {}
            if path == "/api/ahp/calculate":
                matrix = payload.get("ahp_matrix") or AHP_PRESETS["balanced"]["matrix"]
                codes = payload.get("criteria_codes")
                res = calculate_ahp(matrix, codes)
                self._send_json(200, res)
            elif path == "/api/dss/recommend":
                ensure_db_ready()
                res = run_dss_pipeline(payload, db_path=DB_PATH)
                session_id = save_dss_session(res)
                res["session_id"] = session_id
                self._send_json(200, res)
            elif path == "/api/dss/what-if":
                ensure_db_ready()
                res = run_what_if_simulation(payload, db_path=DB_PATH)
                self._send_json(200, res)
            else:
                self._send_json(404, {"error": f"Endpoint POST không tồn tại: {path}"})
        except Exception as exc:
            traceback.print_exc()
            self._send_json(400, {"error": str(exc)})


def run_server(host: str = "127.0.0.1", port: int = 8000):
    ensure_db_ready()
    server = ThreadingHTTPServer((host, port), DSSRequestHandler)
    print(f"=== HUST DSS Job Matching Backend đang chạy tại http://{host}:{port} ===")
    server.serve_forever()


if __name__ == "__main__":
    port_num = int(os.environ.get("PORT", "8000"))
    run_server(host="127.0.0.1", port=port_num)

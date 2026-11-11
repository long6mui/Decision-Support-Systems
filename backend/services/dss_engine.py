# -*- coding: utf-8 -*-
"""
Bộ xử lý Mô hình (Model Base Management System - MBMS) cho Hệ trợ giúp quyết định:
- Phân tích thứ bậc AHP (Analytic Hierarchy Process - Saaty)
- Kiểm tra và gợi ý hiệu chỉnh tỷ số nhất quán (CR < 0.10)
- Lọc ràng buộc cứng (Hard Constraints) & Nới lỏng thông minh (Constraint Relaxation)
- Lượng hóa độ khớp Hồ sơ Sinh viên - Việc làm trên 6 tiêu chí (C1..C6)
- Xếp hạng đa tiêu chí bằng TOPSIS & đối chiếu với SAW
- Phân tích Khoảng trống Kỹ năng (Skill Gap Analysis) & Mô phỏng What-If (Sensitivity Analysis)
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

DB_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "database" / "dss_job_matching.db"

# Bảng chỉ số ngẫu nhiên RI (Random Index) chuẩn của Thomas L. Saaty (n = 1..10)
SAATY_RI_TABLE = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}

# Ma trận tương thích giữa các ngành đào tạo (Major Affinity Matrix)
MAJOR_AFFINITY = {
    "IT1": {"IT1": 1.00, "IT2": 0.92, "DS1": 0.90, "EE1": 0.65, "EE2": 0.60, "ME1": 0.50, "EM1": 0.72, "EM2": 0.55},
    "IT2": {"IT2": 1.00, "IT1": 0.92, "DS1": 0.82, "EM1": 0.78, "EE1": 0.68, "EE2": 0.60, "ME1": 0.52, "EM2": 0.58},
    "DS1": {"DS1": 1.00, "IT1": 0.92, "IT2": 0.82, "EM1": 0.80, "EM2": 0.72, "EE2": 0.62, "EE1": 0.58, "ME1": 0.50},
    "EE1": {"EE1": 1.00, "EE2": 0.85, "IT2": 0.72, "IT1": 0.68, "ME1": 0.78, "DS1": 0.58, "EM1": 0.45, "EM2": 0.40},
    "EE2": {"EE2": 1.00, "EE1": 0.85, "ME1": 0.88, "IT2": 0.65, "IT1": 0.62, "DS1": 0.60, "EM1": 0.48, "EM2": 0.45},
    "ME1": {"ME1": 1.00, "EE2": 0.88, "EE1": 0.78, "IT2": 0.55, "IT1": 0.50, "DS1": 0.48, "EM2": 0.52, "EM1": 0.45},
    "EM1": {"EM1": 1.00, "EM2": 0.88, "IT2": 0.78, "DS1": 0.80, "IT1": 0.70, "EE2": 0.45, "EE1": 0.42, "ME1": 0.40},
    "EM2": {"EM2": 1.00, "EM1": 0.88, "DS1": 0.72, "IT2": 0.60, "IT1": 0.55, "ME1": 0.50, "EE2": 0.45, "EE1": 0.40},
}

# Các cấu hình Ma trận So sánh Cặp AHP Mẫu (6x6 cho C1..C6) đều đảm bảo CR < 0.05
AHP_PRESETS: Dict[str, Dict[str, Any]] = {
    "balanced": {
        "key": "balanced",
        "name": "Cân bằng Đa mục tiêu (Khuyến nghị)",
        "description": "Cân bằng hài hòa giữa Độ khớp kỹ năng (C1), Thu nhập (C2), Độ hợp hồ sơ (C3), Đào tạo (C4) và Môi trường làm việc (C5, C6).",
        "matrix": [
            [1.0,   1.5,   2.0,   2.0,   3.0,   3.0],
            [1/1.5, 1.0,   1.5,   1.5,   2.5,   2.5],
            [1/2.0, 1/1.5, 1.0,   1.0,   2.0,   2.0],
            [1/2.0, 1/1.5, 1.0,   1.0,   2.0,   2.0],
            [1/3.0, 1/2.5, 1/2.0, 1/2.0, 1.0,   1.2],
            [1/3.0, 1/2.5, 1/2.0, 1/2.0, 1/1.2, 1.0],
        ],
    },
    "income_focused": {
        "key": "income_focused",
        "name": "Ưu tiên Thu nhập & Đãi ngộ Tài chính",
        "description": "Đặt trọng tâm cao nhất vào Mức lương khởi điểm (C2) và Độ khớp kỹ năng (C1), sẵn sàng chấp nhận áp lực hoặc đi xa hơn.",
        "matrix": [
            [1.0,   0.5,   2.0,   2.0,   3.0,   4.0],
            [2.0,   1.0,   3.0,   3.0,   4.0,   5.0],
            [1/2.0, 1/3.0, 1.0,   1.0,   2.0,   2.5],
            [1/2.0, 1/3.0, 1.0,   1.0,   2.0,   2.5],
            [1/3.0, 1/4.0, 1/2.0, 1/2.0, 1.0,   1.5],
            [1/4.0, 1/5.0, 1/2.5, 1/2.5, 1/1.5, 1.0],
        ],
    },
    "growth_focused": {
        "key": "growth_focused",
        "name": "Ưu tiên Đào tạo, Mentorship & Phát triển Sự nghiệp",
        "description": "Ưu tiên hàng đầu cho Cơ hội đào tạo & Thăng tiến (C4) và Độ khớp kỹ năng chuyên môn (C1) cho giai đoạn đầu ra trường.",
        "matrix": [
            [1.0,   2.0,   2.0,   1.0,   3.0,   3.5],
            [1/2.0, 1.0,   1.0,   0.5,   2.0,   2.0],
            [1/2.0, 1.0,   1.0,   0.5,   2.0,   2.0],
            [1.0,   2.0,   2.0,   1.0,   3.0,   3.5],
            [1/3.0, 1/2.0, 1/2.0, 1/3.0, 1.0,   1.5],
            [1/3.5, 1/2.0, 1/2.0, 1/3.5, 1/1.5, 1.0],
        ],
    },
    "skill_fit_focused": {
        "key": "skill_fit_focused",
        "name": "Ưu tiên Đúng Chuyên ngành & Thế mạnh Kỹ thuật",
        "description": "Tập trung tối đa vào công việc khớp nhất với bộ kỹ năng hiện có (C1) và nền tảng học vấn/chuyên ngành (C3).",
        "matrix": [
            [1.0,   2.5,   1.5,   2.5,   4.0,   4.0],
            [1/2.5, 1.0,   0.6,   1.0,   2.0,   2.0],
            [1/1.5, 1/0.6, 1.0,   2.0,   3.0,   3.0],
            [1/2.5, 1.0,   1/2.0, 1.0,   2.0,   2.0],
            [1/4.0, 1/2.0, 1/3.0, 1/2.0, 1.0,   1.0],
            [1/4.0, 1/2.0, 1/3.0, 1/2.0, 1.0,   1.0],
        ],
    },
    "work_life_balance": {
        "key": "work_life_balance",
        "name": "Ưu tiên Cân bằng Cuộc sống, Phúc lợi & Gần nhà",
        "description": "Ưu tiên công việc có môi trường phúc lợi tốt (C5), ít áp lực OT và khoảng cách di chuyển gần/Hybrid (C6).",
        "matrix": [
            [1.0,   1.5,   1.5,   1.0,   0.7,   0.6],
            [1/1.5, 1.0,   1.0,   1.0,   0.5,   0.5],
            [1/1.5, 1.0,   1.0,   1.0,   0.5,   0.5],
            [1.0,   1.0,   1.0,   1.0,   0.6,   0.5],
            [1/0.7, 2.0,   2.0,   1/0.6, 1.0,   1.0],
            [1/0.6, 2.0,   2.0,   2.0,   1.0,   1.0],
        ],
    },
}


def get_db_connection(db_path: Path = DB_DEFAULT_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_ahp(matrix_input: List[List[float]], criteria_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Thực hiện thuật toán AHP (Analytic Hierarchy Process) của Thomas Saaty:
    1. Chuẩn hóa ma trận so sánh cặp A (đảm bảo a_ii = 1 và a_ji = 1 / a_ij).
    2. Tính ma trận chuẩn hóa theo cột và vector trọng số w.
    3. Tính vector tổng trọng số Aw, lambda_max, chỉ số nhất quán CI và tỷ số nhất quán CR.
    4. Nếu CR >= 0.10, xác định cặp tiêu chí (i, j) có độ lệch lớn nhất so với tỷ lệ w_i / w_j để gợi ý sửa.
    """
    A = np.array(matrix_input, dtype=float)
    n = A.shape[0]
    if A.shape[0] != A.shape[1]:
        raise ValueError("Ma trận so sánh cặp AHP phải là ma trận vuông.")

    if criteria_codes is None:
        criteria_codes = [f"C{i+1}" for i in range(n)]

    # Đảm bảo đường chéo bằng 1 và đối xứng nghịch đảo từ tam giác trên
    for i in range(n):
        A[i, i] = 1.0
        for j in range(i + 1, n):
            val = max(1.0 / 9.0, min(9.0, float(A[i, j])))
            A[i, j] = val
            A[j, i] = 1.0 / val

    # Bước 1: Tính tổng từng cột và chuẩn hóa ma trận theo cột
    col_sums = A.sum(axis=0)
    normalized_matrix = A / col_sums

    # Bước 2: Vector trọng số ưu tiên (Trung bình hàng của ma trận chuẩn hóa)
    weights = normalized_matrix.mean(axis=1)
    weights = weights / weights.sum()

    # Bước 3: Tính vector nhất quán và lambda_max
    weighted_sum_vector = A @ weights
    consistency_vector = weighted_sum_vector / weights
    lambda_max = float(np.mean(consistency_vector))

    # Bước 4: Tính CI và CR
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = SAATY_RI_TABLE.get(n, 1.24)
    cr = ci / ri if ri > 0 else 0.0
    is_consistent = bool(cr < 0.10)

    # Bước 5: Tìm cặp tiêu chí mâu thuẫn nhất (phục vụ trợ giúp sửa ma trận khi CR >= 0.10)
    inconsistency_hints = []
    for i in range(n):
        for j in range(i + 1, n):
            ideal_ratio = weights[i] / weights[j] if weights[j] > 0 else 1.0
            actual_ratio = A[i, j]
            rel_error = abs(math.log(actual_ratio) - math.log(ideal_ratio))
            if rel_error > 0.45:
                suggested_val = round(max(1.0 / 9.0, min(9.0, ideal_ratio)), 2)
                inconsistency_hints.append({
                    "pair": f"{criteria_codes[i]} vs {criteria_codes[j]}",
                    "row_index": i,
                    "col_index": j,
                    "current_value": round(float(actual_ratio), 3),
                    "suggested_value": suggested_val,
                    "deviation_score": round(float(rel_error), 3),
                    "message": (
                        f"Cặp ({criteria_codes[i]}, {criteria_codes[j]}) đang đặt {actual_ratio:.2f}, "
                        f"nên điều chỉnh gần {suggested_val} để giảm tỷ số CR."
                    ),
                })

    inconsistency_hints.sort(key=lambda x: x["deviation_score"], reverse=True)

    return {
        "n": n,
        "criteria_codes": criteria_codes,
        "pairwise_matrix": np.round(A, 4).tolist(),
        "column_sums": np.round(col_sums, 4).tolist(),
        "normalized_matrix": np.round(normalized_matrix, 4).tolist(),
        "weights": [round(float(w), 4) for w in weights],
        "weights_map": {criteria_codes[i]: round(float(weights[i]), 4) for i in range(n)},
        "weighted_sum_vector": np.round(weighted_sum_vector, 4).tolist(),
        "consistency_vector": np.round(consistency_vector, 4).tolist(),
        "lambda_max": round(lambda_max, 4),
        "ci": round(float(ci), 4),
        "ri": round(float(ri), 4),
        "cr": round(float(cr), 4),
        "is_consistent": is_consistent,
        "inconsistency_hints": inconsistency_hints[:3],
    }


def evaluate_job_for_student(
    student: Dict[str, Any],
    student_skill_map: Dict[int, int],
    job: Dict[str, Any],
    job_skills: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Lượng hóa giá trị 6 tiêu chí (C1..C6) cho cặp (Sinh viên, Công việc) và phân tích Skill Gap.
    """
    # --- Tiêu chí C1: Độ khớp Kỹ năng Chuyên môn & Công nghệ (0..100) ---
    total_weight = 0.0
    earned_weight = 0.0
    mandatory_missing_count = 0

    matched_skills = []
    partial_skills = []
    missing_skills = []

    for js in job_skills:
        s_id = js["skill_id"]
        s_name = js["skill_name"]
        s_cat = js["skill_category"]
        req_lv = int(js["required_level"])
        imp_w = float(js["importance_weight"])
        is_mand = bool(js["is_mandatory"])

        stu_lv = int(student_skill_map.get(s_id, 0))
        total_weight += imp_w

        if stu_lv >= req_lv:
            # Thưởng nhẹ nếu sinh viên vượt mức yêu cầu (tối đa 1.08 lần trọng số)
            bonus_ratio = min(1.08, 1.0 + 0.04 * (stu_lv - req_lv))
            earned_weight += imp_w * bonus_ratio
            matched_skills.append({
                "skill_id": s_id,
                "skill_name": s_name,
                "category": s_cat,
                "student_level": stu_lv,
                "required_level": req_lv,
                "is_mandatory": is_mand,
                "importance_weight": imp_w,
                "status": "MATCHED",
            })
        elif stu_lv > 0:
            ratio = (stu_lv / req_lv) * 0.85
            earned_weight += imp_w * ratio
            partial_skills.append({
                "skill_id": s_id,
                "skill_name": s_name,
                "category": s_cat,
                "student_level": stu_lv,
                "required_level": req_lv,
                "gap": req_lv - stu_lv,
                "is_mandatory": is_mand,
                "importance_weight": imp_w,
                "status": "PARTIAL",
            })
        else:
            if is_mand:
                mandatory_missing_count += 1
            missing_skills.append({
                "skill_id": s_id,
                "skill_name": s_name,
                "category": s_cat,
                "student_level": 0,
                "required_level": req_lv,
                "gap": req_lv,
                "is_mandatory": is_mand,
                "importance_weight": imp_w,
                "status": "MISSING",
            })

    raw_skill_score = (earned_weight / total_weight * 100.0) if total_weight > 0 else 50.0
    # Hệ số phạt nhẹ cho mỗi kỹ năng bắt buộc còn thiếu hoàn toàn (nhưng không triệt tiêu hoàn toàn để SV thấy lộ trình cải thiện)
    mandatory_penalty = (0.86 ** mandatory_missing_count)
    c1_skill_match = round(max(8.0, min(100.0, raw_skill_score * mandatory_penalty)), 2)

    # --- Tiêu chí C3: Độ phù hợp Học vấn, Chuyên ngành, GPA & Ngoại ngữ (0..10) ---
    stu_major_code = student.get("major_code", "IT1")
    job_major_code = job.get("major_code", "IT1")
    major_fit = MAJOR_AFFINITY.get(stu_major_code, {}).get(job_major_code, 0.55) * 10.0

    stu_gpa = float(student.get("gpa", 3.0))
    req_gpa = float(job.get("min_gpa", 2.5))
    if stu_gpa >= req_gpa:
        gpa_fit = min(10.0, 8.0 + (stu_gpa - req_gpa) * 2.5)
    else:
        gpa_fit = max(3.0, 8.0 - (req_gpa - stu_gpa) * 6.0)

    stu_eng = int(student.get("english_tier", 3))
    req_eng = int(job.get("min_english_tier", 3))
    if stu_eng >= req_eng:
        eng_fit = min(10.0, 8.2 + (stu_eng - req_eng) * 0.9)
    else:
        eng_fit = max(3.0, 8.2 - (req_eng - stu_eng) * 2.2)

    stu_exp = int(student.get("internship_months", 3))
    req_exp = int(job.get("min_exp_months", 0))
    if stu_exp >= req_exp:
        exp_fit = min(10.0, 8.5 + min(1.5, (stu_exp - req_exp) * 0.25))
    else:
        exp_fit = max(3.5, 8.5 - (req_exp - stu_exp) * 0.8)

    c3_academic_fit = round(0.40 * major_fit + 0.25 * gpa_fit + 0.20 * eng_fit + 0.15 * exp_fit, 2)

    # --- Tiêu chí C2: Mức Thu nhập Kỳ vọng dành cho Sinh viên (Triệu VNĐ/tháng) ---
    sal_min = float(job["salary_min"])
    sal_max = float(job["salary_max"])
    # Nội suy mức offer dự kiến theo năng lực tổng hợp của ứng viên (kỹ năng 65% + hồ sơ học vấn 35%)
    competency_factor = min(1.0, max(0.0, 0.65 * (c1_skill_match / 100.0) + 0.35 * (c3_academic_fit / 10.0)))
    c2_expected_salary = round(sal_min + (sal_max - sal_min) * competency_factor, 2)

    # --- Tiêu chí C4: Cơ hội Đào tạo, Mentorship & Thăng tiến (1..10) ---
    base_training = float(job["training_score"])
    # Điều chỉnh nhẹ: Nếu SV mới có ít kinh nghiệm (<4 tháng), vị trí Fresher/Intern/MT mang lại giá trị đào tạo sát sườn hơn Junior
    level_bonus = 0.3 if (stu_exp <= 4 and job["level"] in ("Fresher", "Management Trainee")) else 0.0
    c4_growth = round(min(10.0, max(1.0, base_training + level_bonus)), 2)

    # --- Tiêu chí C5: Phúc lợi, Văn hóa & Uy tín Doanh nghiệp (1..10) ---
    comp_rating_10 = float(job["company_rating"]) * 2.0
    c5_welfare = round(min(10.0, max(1.0, 0.70 * float(job["welfare_score"]) + 0.30 * comp_rating_10)), 2)

    # --- Tiêu chí C6 (COST): Chi phí Khoảng cách Di chuyển & Áp lực OT (1..10, càng nhỏ càng tốt) ---
    raw_dist_km = float(job["distance_km_from_center"])
    work_mode = job["work_mode"]
    if work_mode == "Remote":
        effective_dist_km = raw_dist_km * 0.25
    elif work_mode == "Hybrid":
        effective_dist_km = raw_dist_km * 0.65
    else:
        effective_dist_km = raw_dist_km

    dist_cost_10 = min(10.0, max(1.0, effective_dist_km / 2.0))
    pressure_cost_10 = float(job["overtime_pressure_score"])
    c6_cost = round(0.45 * dist_cost_10 + 0.55 * pressure_cost_10, 2)

    return {
        "criteria_values": {
            "C1": c1_skill_match,
            "C2": c2_expected_salary,
            "C3": c3_academic_fit,
            "C4": c4_growth,
            "C5": c5_welfare,
            "C6": c6_cost,
        },
        "skill_analysis": {
            "matched_count": len(matched_skills),
            "partial_count": len(partial_skills),
            "missing_count": len(missing_skills),
            "total_required": len(job_skills),
            "mandatory_missing_count": mandatory_missing_count,
            "matched_skills": matched_skills,
            "partial_skills": partial_skills,
            "missing_skills": missing_skills,
        },
        "academic_breakdown": {
            "major_fit": round(major_fit, 2),
            "gpa_fit": round(gpa_fit, 2),
            "english_fit": round(eng_fit, 2),
            "experience_fit": round(exp_fit, 2),
        },
    }


def run_topsis(
    evaluated_jobs: List[Dict[str, Any]],
    weights: List[float],
    criteria_types: List[str],
    criteria_codes: List[str],
) -> Dict[str, Any]:
    """
    Thực thi thuật toán TOPSIS (Technique for Order Preference by Similarity to Ideal Solution):
    - Bước 1: Lập ma trận quyết định X = [x_ij] kích thước (m x n)
    - Bước 2: Chuẩn hóa vector Euclid r_ij = x_ij / sqrt(sum(x_kj^2))
    - Bước 3: Tính ma trận chuẩn hóa có trọng số v_ij = w_j * r_ij
    - Bước 4: Xác định giải pháp lý tưởng tốt A+ và giải pháp lý tưởng xấu A-
    - Bước 5: Tính khoảng cách Euclid D_i+ và D_i-
    - Bước 6: Tính hệ số tương tự C_i* = D_i- / (D_i+ + D_i-) và xếp hạng
    Đồng thời tính điểm SAW (Simple Additive Weighting) để đối chứng đa mô hình.
    """
    m = len(evaluated_jobs)
    n = len(criteria_codes)
    if m == 0:
        return {
            "ranked_jobs": [],
            "matrices": {},
        }

    X = np.zeros((m, n), dtype=float)
    for i, item in enumerate(evaluated_jobs):
        for j, code in enumerate(criteria_codes):
            X[i, j] = float(item["evaluation"]["criteria_values"][code])

    # Bước 2: Chuẩn hóa vector
    col_norms = np.linalg.norm(X, axis=0)
    col_norms_safe = np.where(col_norms == 0, 1.0, col_norms)
    R = X / col_norms_safe

    # Bước 3: Nhân trọng số AHP
    W = np.array(weights, dtype=float)
    W = W / W.sum()
    V = R * W

    # Bước 4: Tìm A+ và A-
    ideal_best = np.zeros(n, dtype=float)
    ideal_worst = np.zeros(n, dtype=float)
    for j in range(n):
        if criteria_types[j] == "BENEFIT":
            ideal_best[j] = np.max(V[:, j])
            ideal_worst[j] = np.min(V[:, j])
        else:  # COST
            ideal_best[j] = np.min(V[:, j])
            ideal_worst[j] = np.max(V[:, j])

    # Bước 5: Tính khoảng cách Euclid D+ và D-
    d_plus = np.sqrt(np.sum((V - ideal_best) ** 2, axis=1))
    d_minus = np.sqrt(np.sum((V - ideal_worst) ** 2, axis=1))

    # Bước 6: Hệ số gần gũi C*
    denom = d_plus + d_minus
    c_star = np.where(denom > 0, d_minus / denom, 0.5)

    # Tính thêm điểm SAW (Simple Additive Weighting) chuẩn hóa Min-Max để đối chiếu trong báo cáo
    saw_scores = np.zeros(m, dtype=float)
    for j in range(n):
        c_min = np.min(X[:, j])
        c_max = np.max(X[:, j])
        if c_max > c_min:
            if criteria_types[j] == "BENEFIT":
                norm_col = (X[:, j] - c_min) / (c_max - c_min)
            else:
                norm_col = (c_max - X[:, j]) / (c_max - c_min)
        else:
            norm_col = np.ones(m, dtype=float)
        saw_scores += W[j] * norm_col

    saw_order = np.argsort(-saw_scores)
    saw_rank_map = {int(job_idx): int(rk + 1) for rk, job_idx in enumerate(saw_order)}

    # Gắn kết quả vào từng phương án và sắp xếp giảm dần theo C*
    enriched = []
    for i, item in enumerate(evaluated_jobs):
        job_copy = dict(item)
        job_copy["topsis"] = {
            "d_plus": round(float(d_plus[i]), 5),
            "d_minus": round(float(d_minus[i]), 5),
            "c_star": round(float(c_star[i]), 5),
            "match_percentage": round(float(c_star[i]) * 100.0, 2),
            "saw_score": round(float(saw_scores[i]), 5),
            "saw_rank": saw_rank_map[i],
            "raw_vector": [round(float(x), 3) for x in X[i]],
            "normalized_vector": [round(float(r), 4) for r in R[i]],
            "weighted_vector": [round(float(v), 4) for v in V[i]],
        }
        enriched.append(job_copy)

    enriched.sort(key=lambda item: item["topsis"]["c_star"], reverse=True)
    for rank_idx, item in enumerate(enriched, start=1):
        item["topsis"]["rank"] = rank_idx
        item["decision_explanation"] = build_decision_explanation(item, ideal_best, ideal_worst, criteria_codes)

    # Đóng gói các ma trận của Top 15 phương án để hiển thị trực quan trên giao diện "White-box DSS Inspector"
    top_k = min(15, len(enriched))
    inspector_rows = []
    for item in enriched[:top_k]:
        inspector_rows.append({
            "job_id": item["id"],
            "job_code": item["job_code"],
            "title": item["title"],
            "company_short": item["company_short"],
            "rank": item["topsis"]["rank"],
            "saw_rank": item["topsis"]["saw_rank"],
            "raw": item["topsis"]["raw_vector"],
            "normalized": item["topsis"]["normalized_vector"],
            "weighted": item["topsis"]["weighted_vector"],
            "d_plus": item["topsis"]["d_plus"],
            "d_minus": item["topsis"]["d_minus"],
            "c_star": item["topsis"]["c_star"],
            "saw_score": item["topsis"]["saw_score"],
        })

    return {
        "ranked_jobs": enriched,
        "matrices": {
            "criteria_codes": criteria_codes,
            "criteria_types": criteria_types,
            "weights": [round(float(w), 4) for w in W],
            "column_norms": [round(float(cn), 4) for cn in col_norms],
            "ideal_best": [round(float(v), 5) for v in ideal_best],
            "ideal_worst": [round(float(v), 5) for v in ideal_worst],
            "inspector_rows": inspector_rows,
        },
    }


def build_decision_explanation(
    job_item: Dict[str, Any],
    ideal_best: np.ndarray,
    ideal_worst: np.ndarray,
    criteria_codes: List[str],
) -> Dict[str, Any]:
    """Tạo lời giải thích tự động vì sao công việc này được xếp hạng cao và cần lưu ý điểm gì."""
    cv = job_item["evaluation"]["criteria_values"]
    sa = job_item["evaluation"]["skill_analysis"]
    strengths = []
    warnings = []

    if cv["C1"] >= 80:
        strengths.append(f"Độ khớp kỹ năng rất cao ({cv['C1']}%), đáp ứng {sa['matched_count']}/{sa['total_required']} kỹ năng.")
    elif cv["C1"] >= 60:
        strengths.append(f"Đáp ứng tốt nền tảng kỹ năng ({cv['C1']}%), có thể bắt nhịp nhanh.")
    else:
        warnings.append(f"Độ khớp kỹ năng hiện tại đạt {cv['C1']}%, cần bổ sung thêm {sa['missing_count'] + sa['partial_count']} kỹ năng.")

    if cv["C2"] >= 16.0:
        strengths.append(f"Mức thu nhập kỳ vọng hấp dẫn (~{cv['C2']} triệu VNĐ/tháng).")
    elif cv["C2"] >= 12.0:
        strengths.append(f"Thu nhập khởi điểm khá tốt (~{cv['C2']} triệu VNĐ/tháng).")

    if cv["C4"] >= 8.5:
        strengths.append(f"Chương trình đào tạo & Mentorship xuất sắc ({cv['C4']}/10).")

    if cv["C5"] >= 8.4:
        strengths.append(f"Môi trường làm việc & đãi ngộ doanh nghiệp uy tín ({cv['C5']}/10).")

    if cv["C6"] <= 4.8:
        strengths.append(f"Chi phí đi lại & áp lực OT thấp ({cv['C6']}/10 - {job_item['work_mode']}).")
    elif cv["C6"] >= 7.0:
        warnings.append(f"Áp lực công việc hoặc khoảng cách di chuyển khá cao ({cv['C6']}/10).")

    if sa["mandatory_missing_count"] > 0:
        missing_mand_names = [s["skill_name"] for s in sa["missing_skills"] if s["is_mandatory"]]
        warnings.append(f"Cần ưu tiên học gấp kỹ năng bắt buộc: {', '.join(missing_mand_names)}.")

    return {
        "strengths": strengths,
        "warnings": warnings,
    }


def load_all_jobs_with_skills(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Tải toàn bộ danh sách công việc kèm thông tin doanh nghiệp, ngành và kỹ năng yêu cầu."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            j.*,
            c.name AS company_name,
            c.short_name AS company_short,
            c.industry AS company_industry,
            c.size_tier AS company_size,
            c.rating AS company_rating,
            m.code AS major_code,
            m.name AS major_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        JOIN majors m ON j.target_major_id = m.id
        ORDER BY j.id ASC
        """
    )
    jobs = [dict(row) for row in cur.fetchall()]

    cur.execute(
        """
        SELECT
            js.job_id,
            js.skill_id,
            js.required_level,
            js.importance_weight,
            js.is_mandatory,
            s.name AS skill_name,
            s.category AS skill_category
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.id
        ORDER BY js.is_mandatory DESC, js.importance_weight DESC
        """
    )
    skills_by_job: Dict[int, List[Dict[str, Any]]] = {}
    for row in cur.fetchall():
        d = dict(row)
        skills_by_job.setdefault(d["job_id"], []).append(d)

    for j in jobs:
        j["required_skills"] = skills_by_job.get(j["id"], [])

    return jobs


def filter_and_evaluate_jobs(
    all_jobs: List[Dict[str, Any]],
    student: Dict[str, Any],
    student_skill_map: Dict[int, int],
    constraints: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Giai đoạn 1 & 2 của DSS:
    - Lọc theo ràng buộc cứng của sinh viên (Mức lương tối thiểu, Hình thức làm việc, Khoảng cách, Cấp độ, Nhóm ngành).
    - Nếu số công việc sau lọc < 8, tự động nới lỏng thông minh (Soft Relaxation) và báo cáo chi tiết.
    """
    min_salary = float(constraints.get("min_expected_salary", student.get("min_expected_salary", 0.0)))
    max_distance = float(constraints.get("max_distance_km", student.get("max_distance_km", 25.0)))
    preferred_work_mode = constraints.get("preferred_work_mode", student.get("preferred_work_mode", "Any"))
    allowed_levels = constraints.get("levels", ["Intern", "Fresher", "Junior", "Management Trainee"])
    strict_major_only = bool(constraints.get("strict_major_only", False))
    stu_major_code = student.get("major_code", "IT1")

    strict_passed = []
    relaxed_candidates = []
    rejection_stats = {
        "total_jobs": len(all_jobs),
        "rejected_by_salary": 0,
        "rejected_by_distance": 0,
        "rejected_by_work_mode": 0,
        "rejected_by_major": 0,
        "rejected_by_level": 0,
    }

    for job in all_jobs:
        eval_res = evaluate_job_for_student(student, student_skill_map, job, job["required_skills"])
        job_with_eval = dict(job)
        job_with_eval["evaluation"] = eval_res

        # Kiểm tra độ liên quan ngành học
        affinity = MAJOR_AFFINITY.get(stu_major_code, {}).get(job["major_code"], 0.5)
        min_affinity = 0.90 if strict_major_only else 0.58
        if affinity < min_affinity:
            rejection_stats["rejected_by_major"] += 1
            continue

        if allowed_levels and job["level"] not in allowed_levels:
            rejection_stats["rejected_by_level"] += 1
            continue

        # Kiểm tra lương kỳ vọng
        salary_ok = job["salary_max"] >= min_salary
        if not salary_ok:
            rejection_stats["rejected_by_salary"] += 1

        # Kiểm tra khoảng cách (Remote luôn thỏa mãn khoảng cách)
        effective_dist = 0.0 if job["work_mode"] == "Remote" else (
            job["distance_km_from_center"] * 0.7 if job["work_mode"] == "Hybrid" else job["distance_km_from_center"]
        )
        distance_ok = effective_dist <= max_distance
        if not distance_ok:
            rejection_stats["rejected_by_distance"] += 1

        # Kiểm tra hình thức làm việc
        mode_ok = (preferred_work_mode in ("Any", "", None)) or (job["work_mode"] == preferred_work_mode)
        if not mode_ok:
            rejection_stats["rejected_by_work_mode"] += 1

        job_with_eval["constraint_check"] = {
            "salary_ok": salary_ok,
            "distance_ok": distance_ok,
            "work_mode_ok": mode_ok,
            "all_strict_passed": bool(salary_ok and distance_ok and mode_ok),
        }

        if salary_ok and distance_ok and mode_ok:
            strict_passed.append(job_with_eval)
        else:
            relaxed_candidates.append(job_with_eval)

    relaxation_applied = False
    final_pool = list(strict_passed)
    if len(final_pool) < 10 and relaxed_candidates:
        relaxation_applied = True
        # Sắp xếp các ứng viên nới lỏng theo điểm độ khớp kỹ năng C1 để bổ sung đủ tập phương án so sánh
        relaxed_candidates.sort(key=lambda x: x["evaluation"]["criteria_values"]["C1"], reverse=True)
        needed = 12 - len(final_pool)
        final_pool.extend(relaxed_candidates[:needed])

    filter_report = {
        **rejection_stats,
        "strict_passed_count": len(strict_passed),
        "evaluated_pool_count": len(final_pool),
        "relaxation_applied": relaxation_applied,
    }
    return final_pool, filter_report


def aggregate_skill_gap_recommendations(ranked_jobs: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Tổng hợp những kỹ năng còn thiếu xuất hiện nhiều nhất trong Top N công việc phù hợp nhất
    để gợi ý lộ trình học tập cụ thể cho sinh viên tốt nghiệp.
    """
    target_jobs = ranked_jobs[:top_n]
    skill_impact: Dict[int, Dict[str, Any]] = {}

    for job in target_jobs:
        sa = job["evaluation"]["skill_analysis"]
        for sk in sa["missing_skills"] + sa["partial_skills"]:
            sid = sk["skill_id"]
            if sid not in skill_impact:
                skill_impact[sid] = {
                    "skill_id": sid,
                    "skill_name": sk["skill_name"],
                    "category": sk["category"],
                    "current_level": sk["student_level"],
                    "recommended_level": sk["required_level"],
                    "appearances_in_top_jobs": 0,
                    "mandatory_in_jobs": 0,
                    "total_importance": 0.0,
                    "affected_jobs": [],
                }
            entry = skill_impact[sid]
            entry["appearances_in_top_jobs"] += 1
            if sk["is_mandatory"]:
                entry["mandatory_in_jobs"] += 1
            entry["recommended_level"] = max(entry["recommended_level"], sk["required_level"])
            entry["total_importance"] = round(entry["total_importance"] + sk["importance_weight"], 2)
            if len(entry["affected_jobs"]) < 4:
                entry["affected_jobs"].append(job["title"])

    recommendations = list(skill_impact.values())
    recommendations.sort(
        key=lambda x: (x["mandatory_in_jobs"], x["appearances_in_top_jobs"], x["total_importance"]),
        reverse=True,
    )
    return recommendations[:10]


def run_dss_pipeline(
    payload: Dict[str, Any],
    db_path: Path = DB_DEFAULT_PATH,
) -> Dict[str, Any]:
    """
    Hàm điều phối toàn bộ quy trình Hệ trợ giúp quyết định (End-to-End DSS Pipeline):
    1. Đọc dữ liệu sinh viên, kỹ năng và tiêu chí từ CSDL (hoặc từ payload tùy chỉnh).
    2. Giải mô hình AHP để lấy trọng số W và kiểm tra tỷ số nhất quán CR.
    3. Lọc ràng buộc cứng và lượng hóa 6 tiêu chí (C1..C6) cho từng công việc.
    4. Giải mô hình TOPSIS (và SAW đối chứng) để xếp hạng các công việc.
    5. Tổng hợp phân tích khoảng trống kỹ năng (Skill Gap Roadmap).
    """
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # Đọc danh mục tiêu chí
    cur.execute("SELECT * FROM criteria ORDER BY id ASC")
    criteria_rows = [dict(r) for r in cur.fetchall()]
    criteria_codes = [r["code"] for r in criteria_rows]
    criteria_types = [r["type"] for r in criteria_rows]

    # Xác định hồ sơ sinh viên
    student_data = payload.get("student")
    if not student_data and payload.get("student_id"):
        cur.execute(
            """
            SELECT sp.*, m.code AS major_code, m.name AS major_name
            FROM student_profiles sp
            JOIN majors m ON sp.major_id = m.id
            WHERE sp.id = ?
            """,
            (int(payload["student_id"]),),
        )
        row = cur.fetchone()
        if row:
            student_data = dict(row)
            cur.execute(
                "SELECT skill_id, proficiency_level FROM student_skills WHERE student_id = ?",
                (student_data["id"],),
            )
            student_data["skills"] = [dict(r) for r in cur.fetchall()]

    if not student_data:
        raise ValueError("Cần cung cấp thông tin hồ sơ sinh viên (student hoặc student_id).")

    # Nếu chỉ có major_id mà chưa có major_code thì tra cứu thêm
    if "major_code" not in student_data and "major_id" in student_data:
        cur.execute("SELECT code, name FROM majors WHERE id = ?", (int(student_data["major_id"]),))
        m_row = cur.fetchone()
        if m_row:
            student_data["major_code"] = m_row["code"]
            student_data["major_name"] = m_row["name"]

    student_skill_map: Dict[int, int] = {}
    for sk in student_data.get("skills", []):
        student_skill_map[int(sk["skill_id"])] = int(sk["proficiency_level"])

    # Giải AHP
    ahp_matrix = payload.get("ahp_matrix")
    preset_key = payload.get("ahp_preset") or student_data.get("persona_preset", "balanced")
    if not ahp_matrix:
        ahp_matrix = AHP_PRESETS.get(preset_key, AHP_PRESETS["balanced"])["matrix"]

    ahp_result = calculate_ahp(ahp_matrix, criteria_codes)

    # Cho phép ghi đè trọng số trực tiếp nếu người dùng dùng thanh trượt trong What-If
    custom_weights = payload.get("DirectWeights") or payload.get("direct_weights")
    if custom_weights and len(custom_weights) == len(criteria_codes):
        w_sum = sum(float(x) for x in custom_weights)
        active_weights = [float(x) / w_sum for x in custom_weights] if w_sum > 0 else ahp_result["weights"]
    else:
        active_weights = ahp_result["weights"]

    # Lọc & đánh giá công việc
    all_jobs = load_all_jobs_with_skills(conn)
    constraints = payload.get("constraints", {})
    evaluated_pool, filter_report = filter_and_evaluate_jobs(
        all_jobs=all_jobs,
        student=student_data,
        student_skill_map=student_skill_map,
        constraints=constraints,
    )

    # Xếp hạng TOPSIS
    topsis_result = run_topsis(
        evaluated_jobs=evaluated_pool,
        weights=active_weights,
        criteria_types=criteria_types,
        criteria_codes=criteria_codes,
    )

    ranked_jobs = topsis_result["ranked_jobs"]
    skill_roadmap = aggregate_skill_gap_recommendations(ranked_jobs, top_n=10)

    conn.close()

    return {
        "student": student_data,
        "criteria": criteria_rows,
        "ahp": ahp_result,
        "filter_report": filter_report,
        "topsis_matrices": topsis_result["matrices"],
        "ranked_jobs": ranked_jobs[:30],
        "total_ranked": len(ranked_jobs),
        "skill_gap_roadmap": skill_roadmap,
    }


def run_what_if_simulation(
    payload: Dict[str, Any],
    db_path: Path = DB_DEFAULT_PATH,
) -> Dict[str, Any]:
    """
    Phân tích độ nhạy (Sensitivity / What-If Analysis):
    So sánh kết quả xếp hạng gốc (Baseline) với kịch bản giả định khi sinh viên:
    - Học thêm hoặc nâng cấp một số kỹ năng (added_skills)
    - Nâng trình độ ngoại ngữ hoặc GPA (modified_student_fields)
    - Thay đổi trọng số ưu tiên giữa các tiêu chí (modified_weights / modified_ahp_matrix)
    """
    baseline_res = run_dss_pipeline(payload, db_path=db_path)

    # Tạo bản sao payload cho kịch bản What-If
    sim_payload = json.loads(json.dumps(payload))
    sim_student = dict(baseline_res["student"])
    existing_skills = {int(s["skill_id"]): int(s["proficiency_level"]) for s in sim_student.get("skills", [])}

    for add_sk in payload.get("added_skills", []):
        sid = int(add_sk["skill_id"])
        lv = int(add_sk.get("proficiency_level", 4))
        existing_skills[sid] = max(existing_skills.get(sid, 0), lv)

    sim_student["skills"] = [{"skill_id": k, "proficiency_level": v} for k, v in existing_skills.items()]

    if payload.get("simulated_english_tier"):
        sim_student["english_tier"] = int(payload["simulated_english_tier"])
    if payload.get("simulated_internship_months") is not None:
        sim_student["internship_months"] = int(payload["simulated_internship_months"])

    sim_payload["student"] = sim_student
    if payload.get("simulated_weights"):
        sim_payload["direct_weights"] = payload["simulated_weights"]
    if payload.get("simulated_ahp_matrix"):
        sim_payload["ahp_matrix"] = payload["simulated_ahp_matrix"]

    simulated_res = run_dss_pipeline(sim_payload, db_path=db_path)

    base_map = {
        j["id"]: {
            "rank": j["topsis"]["rank"],
            "c_star": j["topsis"]["c_star"],
            "c1_skill": j["evaluation"]["criteria_values"]["C1"],
            "c2_salary": j["evaluation"]["criteria_values"]["C2"],
        }
        for j in baseline_res["ranked_jobs"]
    }

    comparison_list = []
    for sim_job in simulated_res["ranked_jobs"][:20]:
        jid = sim_job["id"]
        b_info = base_map.get(jid)
        old_rank = b_info["rank"] if b_info else None
        new_rank = sim_job["topsis"]["rank"]
        old_c_star = b_info["c_star"] if b_info else 0.0
        new_c_star = sim_job["topsis"]["c_star"]

        comparison_list.append({
            "job_id": jid,
            "job_code": sim_job["job_code"],
            "title": sim_job["title"],
            "company_short": sim_job["company_short"],
            "level": sim_job["level"],
            "old_rank": old_rank,
            "new_rank": new_rank,
            "rank_delta": (old_rank - new_rank) if old_rank is not None else 0,
            "old_c_star": round(old_c_star, 4),
            "new_c_star": round(new_c_star, 4),
            "c_star_delta": round(new_c_star - old_c_star, 4),
            "old_skill_score": b_info["c1_skill"] if b_info else 0.0,
            "new_skill_score": sim_job["evaluation"]["criteria_values"]["C1"],
            "old_salary": b_info["c2_salary"] if b_info else sim_job["evaluation"]["criteria_values"]["C2"],
            "new_salary": sim_job["evaluation"]["criteria_values"]["C2"],
        })

    return {
        "baseline_top5": baseline_res["ranked_jobs"][:5],
        "simulated_top5": simulated_res["ranked_jobs"][:5],
        "comparison": comparison_list,
        "simulated_weights": simulated_res["topsis_matrices"]["weights"],
    }


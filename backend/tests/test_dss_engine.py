# -*- coding: utf-8 -*-
"""
Kiểm thử tự động (Unit & Integration Tests) cho Bộ xử lý Mô hình DSS (AHP + TOPSIS + Skill Matching + What-If)
"""

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.seed_data import DB_PATH, init_database
from backend.services.dss_engine import (
    AHP_PRESETS,
    calculate_ahp,
    run_dss_pipeline,
    run_what_if_simulation,
)


class TestDSSEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            init_database(force_recreate=True)

    def test_ahp_presets_consistency(self):
        """Tất cả các cấu hình AHP mẫu phải có tổng trọng số = 1.0 và tỷ số nhất quán CR < 0.10."""
        for key, preset in AHP_PRESETS.items():
            res = calculate_ahp(preset["matrix"])
            self.assertAlmostEqual(sum(res["weights"]), 1.0, places=3)
            self.assertTrue(res["is_consistent"], f"Preset {key} không đạt CR < 0.10: CR={res['cr']}")
            self.assertLess(res["cr"], 0.10)

    def test_ahp_inconsistent_detection(self):
        """Kiểm tra phát hiện mâu thuẫn khi người dùng nhập ma trận bắc cầu sai lệch (C1 > C2, C2 > C3 nhưng C3 >> C1)."""
        bad_matrix = [
            [1.0, 7.0, 0.125, 2.0, 3.0, 3.0],
            [1/7.0, 1.0, 6.0, 2.0, 2.0, 2.0],
            [8.0, 1/6.0, 1.0, 2.0, 2.0, 2.0],
            [0.5, 0.5, 0.5, 1.0, 1.0, 1.0],
            [1/3.0, 0.5, 0.5, 1.0, 1.0, 1.0],
            [1/3.0, 0.5, 0.5, 1.0, 1.0, 1.0],
        ]
        res = calculate_ahp(bad_matrix)
        self.assertFalse(res["is_consistent"])
        self.assertGreaterEqual(res["cr"], 0.10)
        self.assertGreater(len(res["inconsistency_hints"]), 0)

    def test_end_to_end_dss_pipeline_all_profiles(self):
        """Chạy thử nghiệm toàn bộ 10 hồ sơ sinh viên mẫu qua quy trình AHP + TOPSIS."""
        for student_id in range(1, 11):
            result = run_dss_pipeline({"student_id": student_id})
            self.assertGreater(len(result["ranked_jobs"]), 5)
            top1 = result["ranked_jobs"][0]
            self.assertEqual(top1["topsis"]["rank"], 1)
            self.assertGreaterEqual(top1["topsis"]["c_star"], 0.0)
            self.assertLessEqual(top1["topsis"]["c_star"], 1.0)
            # Đảm bảo thứ tự giảm dần của C*
            c_stars = [j["topsis"]["c_star"] for j in result["ranked_jobs"]]
            self.assertEqual(c_stars, sorted(c_stars, reverse=True))

    def test_what_if_simulation_skill_improvement(self):
        """Kiểm tra khi sinh viên học thêm kỹ năng còn thiếu thì điểm độ khớp C1 phải tăng hoặc giữ nguyên."""
        base = run_dss_pipeline({"student_id": 2})
        roadmap = base["skill_gap_roadmap"]
        self.assertGreater(len(roadmap), 0)
        missing_skill_id = roadmap[0]["skill_id"]

        sim = run_what_if_simulation({
            "student_id": 2,
            "added_skills": [{"skill_id": missing_skill_id, "proficiency_level": 5}],
        })
        self.assertGreater(len(sim["comparison"]), 0)
        improved_any = any(item["new_skill_score"] > item["old_skill_score"] for item in sim["comparison"])
        self.assertTrue(improved_any, "Phải có ít nhất 1 công việc tăng điểm kỹ năng C1 khi học thêm kỹ năng còn thiếu.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


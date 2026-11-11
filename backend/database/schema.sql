-- =============================================================================
-- HỆ TRỢ GIÚP QUYẾT ĐỊNH (DSS): TRỢ GIÚP SINH VIÊN TỐT NGHIỆP TÌM VIỆC LÀM
-- Lược đồ Cơ sở dữ liệu Quan hệ (SQLite / PostgreSQL Compatible)
-- Đại học Bách Khoa Hà Nội (HUST)
-- =============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS dss_sessions;
DROP TABLE IF EXISTS student_skills;
DROP TABLE IF EXISTS student_profiles;
DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS majors;
DROP TABLE IF EXISTS criteria;

-- 1. Bảng Ngành Đào tạo (MAJORS)
CREATE TABLE majors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    faculty TEXT NOT NULL,
    description TEXT
);

-- 2. Bảng Danh mục Kỹ năng (SKILLS)
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN (
        'Programming',
        'Data_AI',
        'Web_Mobile',
        'System_DevOps',
        'Embedded_Hardware',
        'Business_Domain',
        'SoftSkill',
        'Language'
    )),
    description TEXT
);

-- 3. Bảng Doanh nghiệp Tuyển dụng (COMPANIES)
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    short_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    size_tier TEXT NOT NULL CHECK (size_tier IN ('Startup', 'SME', 'Large', 'MNC', 'Enterprise')),
    rating REAL NOT NULL CHECK (rating >= 1.0 AND rating <= 5.0),
    headquarters_district TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT 'Hà Nội',
    website TEXT,
    description TEXT
);

-- 4. Bảng Việc làm Tuyển dụng dành cho SV Tốt nghiệp (JOBS)
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_code TEXT NOT NULL UNIQUE,
    company_id INTEGER NOT NULL,
    target_major_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('Intern', 'Fresher', 'Junior', 'Management Trainee')),
    salary_min REAL NOT NULL,              -- Triệu VNĐ / tháng
    salary_max REAL NOT NULL,              -- Triệu VNĐ / tháng
    min_gpa REAL NOT NULL DEFAULT 2.5,     -- Thang 4.0
    min_english_tier INTEGER NOT NULL DEFAULT 3, -- 1: A1, 2: A2, 3: B1 (TOEIC 500+), 4: B2 (TOEIC 650+/IELTS 6.0), 5: C1 (IELTS 7.0+), 6: C2
    min_exp_months INTEGER NOT NULL DEFAULT 0,   -- Số tháng kinh nghiệm thực tập/làm việc
    district TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT 'Hà Nội',
    distance_km_from_center REAL NOT NULL, -- Khoảng cách ước tính từ khu vực Bách Khoa / Trung tâm (km)
    work_mode TEXT NOT NULL CHECK (work_mode IN ('Onsite', 'Hybrid', 'Remote')),
    training_score REAL NOT NULL CHECK (training_score >= 1.0 AND training_score <= 10.0),         -- Tiêu chí C4: Đào tạo & Lộ trình thăng tiến
    welfare_score REAL NOT NULL CHECK (welfare_score >= 1.0 AND welfare_score <= 10.0),           -- Tiêu chí C5: Phúc lợi & Văn hóa doanh nghiệp
    overtime_pressure_score REAL NOT NULL CHECK (overtime_pressure_score >= 1.0 AND overtime_pressure_score <= 10.0), -- Tiêu chí C6 (Cost): Áp lực & OT
    slots INTEGER NOT NULL DEFAULT 3,
    description TEXT NOT NULL,
    benefits_summary TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (target_major_id) REFERENCES majors(id) ON DELETE RESTRICT
);

-- 5. Bảng Yêu cầu Kỹ năng của từng Việc làm (JOB_SKILLS)
CREATE TABLE job_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    required_level INTEGER NOT NULL CHECK (required_level >= 1 AND required_level <= 5),
    importance_weight REAL NOT NULL DEFAULT 2.0 CHECK (importance_weight >= 0.5 AND importance_weight <= 3.0),
    is_mandatory INTEGER NOT NULL DEFAULT 0 CHECK (is_mandatory IN (0, 1)),
    UNIQUE(job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- 6. Bảng Hồ sơ Sinh viên Tốt nghiệp Mẫu (STUDENT_PROFILES)
CREATE TABLE student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    major_id INTEGER NOT NULL,
    gpa REAL NOT NULL CHECK (gpa >= 0.0 AND gpa <= 4.0),
    english_tier INTEGER NOT NULL CHECK (english_tier >= 1 AND english_tier <= 6),
    english_cert TEXT NOT NULL,
    internship_months INTEGER NOT NULL DEFAULT 0,
    min_expected_salary REAL NOT NULL DEFAULT 8.0,
    preferred_city TEXT NOT NULL DEFAULT 'Hà Nội',
    current_district TEXT NOT NULL DEFAULT 'Hai Bà Trưng',
    max_distance_km REAL NOT NULL DEFAULT 15.0,
    preferred_work_mode TEXT NOT NULL DEFAULT 'Any', -- Any | Onsite | Hybrid | Remote
    career_goal TEXT NOT NULL,
    persona_preset TEXT NOT NULL DEFAULT 'balanced',
    FOREIGN KEY (major_id) REFERENCES majors(id) ON DELETE RESTRICT
);

-- 7. Bảng Kỹ năng Hiện có của Sinh viên (STUDENT_SKILLS)
CREATE TABLE student_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level INTEGER NOT NULL CHECK (proficiency_level >= 1 AND proficiency_level <= 5),
    UNIQUE(student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- 8. Bảng Danh mục Tiêu chí Đánh giá trong Mô hình DSS (CRITERIA)
CREATE TABLE criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('BENEFIT', 'COST')),
    unit TEXT NOT NULL,
    default_weight REAL NOT NULL,
    description TEXT NOT NULL,
    formula_note TEXT NOT NULL
);

-- 9. Bảng Lưu Phiên Tư vấn & Kết quả Ra quyết định (DSS_SESSIONS)
CREATE TABLE dss_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    student_name TEXT NOT NULL,
    ahp_matrix_json TEXT NOT NULL,
    weights_json TEXT NOT NULL,
    lambda_max REAL NOT NULL,
    consistency_index REAL NOT NULL,
    consistency_ratio REAL NOT NULL,
    top_results_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES student_profiles(id) ON DELETE SET NULL
);

CREATE INDEX idx_jobs_major ON jobs(target_major_id);
CREATE INDEX idx_jobs_company ON jobs(company_id);
CREATE INDEX idx_job_skills_job ON job_skills(job_id);
CREATE INDEX idx_job_skills_skill ON job_skills(skill_id);
CREATE INDEX idx_student_skills_student ON student_skills(student_id);


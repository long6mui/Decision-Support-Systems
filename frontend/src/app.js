/**
 * HUST CareerDSS - Ứng dụng Giao diện Hệ Trợ Giúp Quyết Định Tìm Việc Làm Cho Sinh Viên Tốt Nghiệp
 * Tích hợp đầy đủ:
 * - Tab 1: Hồ sơ Năng lực Sinh viên & Bộ lọc Ràng buộc Cứng (Hard Constraints)
 * - Tab 2: Ma trận So sánh Cặp AHP (Saaty 1-9), Kiểm định Tỷ số Nhất quán CR < 0.10 & Tự động Gợi ý Hiệu chỉnh
 * - Tab 3: Bảng Xếp hạng TOPSIS, Biểu đồ Radar 6 trục, Biểu đồ Khoảng cách Lý tưởng (D+, D-) & Chi tiết Skill Gap
 * - Tab 4: Giải trình Toán học White-box (Ma trận X, R, V, A+, A-, D+, D-, C*, đối chiếu TOPSIS vs SAW)
 * - Tab 5: Lộ trình Bù đắp Kỹ năng (Skill Gap Roadmap) & Mô phỏng Độ nhạy (What-If Analysis)
 */

(function () {
  const API_BASE = "http://127.0.0.1:8000/api";

  const SAATY_OPTIONS = [
    { val: 0.1111, label: "1/9 (Kém tuyệt đối)" },
    { val: 0.125, label: "1/8" },
    { val: 0.1429, label: "1/7 (Kém rất nhiều)" },
    { val: 0.1667, label: "1/6" },
    { val: 0.2, label: "1/5 (Kém nhiều)" },
    { val: 0.25, label: "1/4" },
    { val: 0.3333, label: "1/3 (Kém vừa phải)" },
    { val: 0.5, label: "1/2 (Kém nhẹ)" },
    { val: 0.6667, label: "2/3" },
    { val: 1.0, label: "1 (Ngang nhau)" },
    { val: 1.5, label: "1.5 (Hơn nhẹ)" },
    { val: 2.0, label: "2 (Hơn nhẹ - vừa)" },
    { val: 2.5, label: "2.5" },
    { val: 3.0, label: "3 (Quan trọng hơn vừa)" },
    { val: 3.5, label: "3.5" },
    { val: 4.0, label: "4 (Quan trọng hơn khá)" },
    { val: 5.0, label: "5 (Quan trọng hơn nhiều)" },
    { val: 6.0, label: "6" },
    { val: 7.0, label: "7 (Rất quan trọng)" },
    { val: 8.0, label: "8" },
    { val: 9.0, label: "9 (Tuyệt đối quan trọng)" },
  ];

  const ENGLISH_TIERS = [
    { tier: 1, label: "Bậc 1 - A1 (Cơ bản)" },
    { tier: 2, label: "Bậc 2 - A2 (TOEIC ~400)" },
    { tier: 3, label: "Bậc 3 - B1 (TOEIC 500-600 / Chuẩn đầu ra)" },
    { tier: 4, label: "Bậc 4 - B2 (TOEIC 650-780 / IELTS 6.0)" },
    { tier: 5, label: "Bậc 5 - C1 (TOEIC 800+ / IELTS 7.0+)" },
    { tier: 6, label: "Bậc 6 - C2 (Thành thạo bản ngữ / IELTS 8.0+)" },
  ];

  const state = {
    apiConnected: false,
    snapshot: window.DSS_DB_SNAPSHOT || null,
    activeTab: "dashboard", // profile | ahp | dashboard | math | whatif
    selectedStudentId: 1,
    student: null,
    constraints: {
      min_expected_salary: 12.0,
      max_distance_km: 15.0,
      preferred_work_mode: "Any",
      levels: ["Intern", "Fresher", "Junior", "Management Trainee"],
      strict_major_only: false,
    },
    activeSkillCategory: "ALL",
    skillSearchText: "",
    activeAhpPreset: "growth_focused",
    ahpMatrix: null,
    dssResult: null,
    selectedJobId: null,
    whatIfAddedSkills: {}, // skill_id -> level
    whatIfEnglishTier: null,
    whatIfInternMonths: null,
    whatIfResult: null,
  };

  function clone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  async function checkBackendAndInit() {
    // Khởi tạo từ snapshot trước để giao diện hiển thị tức thì (0ms delay)
    if (state.snapshot && state.snapshot.student_profiles.length > 0) {
      selectStudentProfile(1, false);
    }

    // Thử kết nối tới Python SQLite REST API
    try {
      const resp = await fetch(`${API_BASE}/health`, { method: "GET" });
      if (resp.ok) {
        state.apiConnected = true;
        const bootResp = await fetch(`${API_BASE}/bootstrap`);
        if (bootResp.ok) {
          const bootData = await bootResp.json();
          const jobsResp = await fetch(`${API_BASE}/jobs`);
          const jobsData = jobsResp.ok ? await jobsResp.json() : { jobs: state.snapshot.jobs };
          state.snapshot = Object.assign({}, bootData, {
            jobs: jobsData.jobs && jobsData.jobs.length > 0 ? jobsData.jobs : state.snapshot.jobs,
          });
        }
      }
    } catch (e) {
      state.apiConnected = false;
    }

    await recomputeDSS();
    renderApp();
  }

  function selectStudentProfile(studentId, triggerRecompute = true) {
    state.selectedStudentId = Number(studentId);
    const found = state.snapshot.student_profiles.find(
      (s) => Number(s.id) === state.selectedStudentId
    );
    if (!found) return;

    state.student = clone(found);
    state.constraints = {
      min_expected_salary: Number(found.min_expected_salary || 10.0),
      max_distance_km: Number(found.max_distance_km || 15.0),
      preferred_work_mode: found.preferred_work_mode || "Any",
      levels: ["Intern", "Fresher", "Junior", "Management Trainee"],
      strict_major_only: false,
    };
    const presetKey = found.persona_preset || "balanced";
    state.activeAhpPreset = presetKey;
    const presetObj =
      state.snapshot.ahp_presets[presetKey] || state.snapshot.ahp_presets.balanced;
    state.ahpMatrix = clone(presetObj.matrix);

    state.whatIfAddedSkills = {};
    state.whatIfEnglishTier = found.english_tier;
    state.whatIfInternMonths = found.internship_months;
    state.whatIfResult = null;

    if (triggerRecompute) {
      recomputeDSS().then(() => renderApp());
    }
  }

  async function recomputeDSS() {
    const payload = {
      student: state.student,
      ahp_matrix: state.ahpMatrix,
      ahp_preset: state.activeAhpPreset,
      constraints: state.constraints,
    };

    if (state.apiConnected) {
      try {
        const resp = await fetch(`${API_BASE}/dss/recommend`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (resp.ok) {
          state.dssResult = await resp.json();
        } else {
          state.dssResult = window.DSSClientEngine.runPipelineLocal(state.snapshot, payload);
        }
      } catch (e) {
        state.dssResult = window.DSSClientEngine.runPipelineLocal(state.snapshot, payload);
      }
    } else {
      state.dssResult = window.DSSClientEngine.runPipelineLocal(state.snapshot, payload);
    }

    if (state.dssResult && state.dssResult.ranked_jobs.length > 0) {
      const stillExists = state.dssResult.ranked_jobs.some(
        (j) => j.id === state.selectedJobId
      );
      if (!stillExists) {
        state.selectedJobId = state.dssResult.ranked_jobs[0].id;
      }
    }

    // Tự động tính sẵn kịch bản What-If mặc định từ Top 2 kỹ năng còn thiếu trong Roadmap
    if (
      Object.keys(state.whatIfAddedSkills).length === 0 &&
      state.dssResult &&
      state.dssResult.skill_gap_roadmap.length > 0
    ) {
      state.dssResult.skill_gap_roadmap.slice(0, 2).forEach((item) => {
        state.whatIfAddedSkills[item.skill_id] = item.recommended_level;
      });
    }
    await recomputeWhatIf();
  }

  async function recomputeWhatIf() {
    const addedList = Object.entries(state.whatIfAddedSkills).map(([sid, lv]) => ({
      skill_id: Number(sid),
      proficiency_level: Number(lv),
    }));
    const payload = {
      student: state.student,
      ahp_matrix: state.ahpMatrix,
      constraints: state.constraints,
      added_skills: addedList,
      simulated_english_tier: state.whatIfEnglishTier || state.student.english_tier,
      simulated_internship_months:
        state.whatIfInternMonths !== null
          ? state.whatIfInternMonths
          : state.student.internship_months,
    };

    if (state.apiConnected) {
      try {
        const resp = await fetch(`${API_BASE}/dss/what-if`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (resp.ok) {
          state.whatIfResult = await resp.json();
          return;
        }
      } catch (e) {
        // Fallback local
      }
    }
    state.whatIfResult = window.DSSClientEngine.runWhatIfLocal(state.snapshot, payload);
  }

  // =========================================================================
  // SVG CHARTS (Radar Chart & Distance Bar Chart)
  // =========================================================================
  function buildRadarChartSVG(selectedJob, top1Job) {
    if (!selectedJob) return "";
    const width = 360;
    const height = 290;
    const cx = width / 2;
    const cy = height / 2 + 5;
    const radius = 102;
    const labels = [
      "C1: Kỹ năng",
      "C2: Thu nhập",
      "C3: Hồ sơ",
      "C4: Đào tạo",
      "C5: Phúc lợi",
      "C6: Ít áp lực/Gần",
    ];

    function normalizeJobToRadar(job) {
      const cv = job.evaluation.criteria_values;
      return [
        Math.min(1.0, cv.C1 / 100.0),
        Math.min(1.0, cv.C2 / 25.0),
        Math.min(1.0, cv.C3 / 10.0),
        Math.min(1.0, cv.C4 / 10.0),
        Math.min(1.0, cv.C5 / 10.0),
        Math.max(0.1, Math.min(1.0, (11.0 - cv.C6) / 10.0)), // Đảo ngược C6 (Cost) để càng ra ngoài càng tốt trên biểu đồ Radar
      ];
    }

    const selVals = normalizeJobToRadar(selectedJob);
    const top1Vals = top1Job ? normalizeJobToRadar(top1Job) : selVals;

    function getPoint(idx, ratio) {
      const angle = (Math.PI * 2 * idx) / 6 - Math.PI / 2;
      const x = cx + radius * ratio * Math.cos(angle);
      const y = cy + radius * ratio * Math.sin(angle);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }

    let gridPolygons = "";
    [0.25, 0.5, 0.75, 1.0].forEach((level) => {
      const pts = [0, 1, 2, 3, 4, 5].map((i) => getPoint(i, level)).join(" ");
      gridPolygons += `<polygon points="${pts}" fill="none" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="${
        level === 1.0 ? "none" : "3,3"
      }" />`;
    });

    let axesLines = "";
    let axisLabels = "";
    for (let i = 0; i < 6; i++) {
      const endPt = getPoint(i, 1.0).split(",");
      axesLines += `<line x1="${cx}" y1="${cy}" x2="${endPt[0]}" y2="${endPt[1]}" stroke="#cbd5e1" stroke-width="1" />`;

      const lblPt = getPoint(i, 1.24).split(",");
      axisLabels += `<text x="${lblPt[0]}" y="${lblPt[1]}" text-anchor="middle" dominant-baseline="middle" font-size="11" font-weight="600" fill="#334155">${labels[i]}</text>`;
    }

    const top1Polygon = [0, 1, 2, 3, 4, 5].map((i) => getPoint(i, top1Vals[i])).join(" ");
    const selPolygon = [0, 1, 2, 3, 4, 5].map((i) => getPoint(i, selVals[i])).join(" ");

    return `
      <svg viewBox="0 0 ${width} ${height}" width="100%" height="280">
        ${gridPolygons}
        ${axesLines}
        <polygon points="${top1Polygon}" fill="rgba(13, 148, 136, 0.14)" stroke="#0d9488" stroke-width="2" stroke-dasharray="4,3" />
        <polygon points="${selPolygon}" fill="rgba(29, 78, 216, 0.24)" stroke="#1d4ed8" stroke-width="2.5" />
        ${axisLabels}
      </svg>
      <div style="display:flex; justify-content:center; gap:18px; font-size:12px; margin-top:4px;">
        <span><strong style="color:#1d4ed8;">■</strong> Đang chọn (#${selectedJob.topsis.rank})</span>
        <span><strong style="color:#0d9488;">▨</strong> Hạng #1 (${top1Job ? top1Job.company_short : ""})</span>
      </div>
    `;
  }

  // =========================================================================
  // RENDER TABS
  // =========================================================================
  function renderProfileTab() {
    const s = state.student;
    const c = state.constraints;
    const majors = state.snapshot.majors;
    const skills = state.snapshot.skills;

    const stuSkillMap = {};
    (s.skills || []).forEach((sk) => {
      stuSkillMap[Number(sk.skill_id)] = Number(sk.proficiency_level);
    });

    const categories = [
      { key: "ALL", label: "Tất cả (65)" },
      { key: "Programming", label: "Lập trình" },
      { key: "Web_Mobile", label: "Web & Mobile" },
      { key: "Data_AI", label: "Dữ liệu & AI" },
      { key: "System_DevOps", label: "Cloud & DevOps" },
      { key: "Embedded_Hardware", label: "Nhúng, Vi mạch & Tự động hóa" },
      { key: "Business_Domain", label: "BA, ERP & Kinh tế" },
      { key: "SoftSkill", label: "Kỹ năng mềm" },
      { key: "Language", label: "Ngoại ngữ" },
    ];

    const filteredSkills = skills.filter((sk) => {
      if (state.activeSkillCategory !== "ALL" && sk.category !== state.activeSkillCategory) {
        return false;
      }
      if (
        state.skillSearchText &&
        !sk.name.toLowerCase().includes(state.skillSearchText.toLowerCase())
      ) {
        return false;
      }
      return true;
    });

    return `
      <div class="grid-sidebar-main">
        <!-- Cột trái: Thông tin Học vấn & Ràng buộc Cứng -->
        <div style="display:flex; flex-direction:column; gap:16px;">
          <div class="panel-card">
            <div class="panel-header">
              <div>
                <div class="panel-title">1. Hồ sơ Học vấn Sinh viên Tốt nghiệp</div>
                <div class="panel-subtitle">Các biến đầu vào phản ánh năng lực nền tảng của người ra quyết định</div>
              </div>
              <span class="badge badge-blue">MSSV: ${s.student_code}</span>
            </div>

            <div class="form-grid">
              <div class="form-group full">
                <label>Họ và tên Sinh viên / Định hướng</label>
                <input id="inp-student-name" class="form-control" value="${s.full_name}" />
              </div>

              <div class="form-group full">
                <label>Ngành Đào tạo tại ĐHBK Hà Nội (HUST)</label>
                <select id="sel-major" class="form-control">
                  ${majors
                    .map(
                      (m) => `
                    <option value="${m.code}" ${m.code === s.major_code ? "selected" : ""}>
                      [${m.code}] ${m.name}
                    </option>
                  `
                    )
                    .join("")}
                </select>
              </div>

              <div class="form-group">
                <label>Điểm tích lũy GPA (Thang 4.0): <strong>${Number(s.gpa).toFixed(2)}</strong></label>
                <input id="inp-gpa" type="range" min="2.0" max="4.0" step="0.05" value="${s.gpa}" class="form-control" />
              </div>

              <div class="form-group">
                <label>Kinh nghiệm Thực tập / Đồ án: <strong>${s.internship_months} tháng</strong></label>
                <input id="inp-exp" type="range" min="0" max="18" step="1" value="${s.internship_months}" class="form-control" />
              </div>

              <div class="form-group full">
                <label>Trình độ Ngoại ngữ Quy đổi</label>
                <select id="sel-english" class="form-control">
                  ${ENGLISH_TIERS.map(
                    (e) => `
                    <option value="${e.tier}" ${Number(s.english_tier) === e.tier ? "selected" : ""}>
                      ${e.label}
                    </option>
                  `
                  ).join("")}
                </select>
              </div>

              <div class="form-group full">
                <label>Mục tiêu nghề nghiệp (Career Goal)</label>
                <textarea id="inp-goal" rows="2" class="form-control">${s.career_goal || ""}</textarea>
              </div>
            </div>
          </div>

          <div class="panel-card">
            <div class="panel-header">
              <div>
                <div class="panel-title">2. Bộ lọc Ràng buộc Cứng (Hard Constraints)</div>
                <div class="panel-subtitle">Loại bỏ sớm các công việc không phù hợp điều kiện cá nhân</div>
              </div>
              <span class="badge badge-amber">Giai đoạn 1</span>
            </div>

            <div class="form-grid">
              <div class="form-group">
                <label>Lương tối thiểu kỳ vọng: <strong>${c.min_expected_salary} triệu</strong></label>
                <input id="inp-min-sal" type="range" min="5" max="22" step="0.5" value="${c.min_expected_salary}" class="form-control" />
              </div>

              <div class="form-group">
                <label>Khoảng cách tối đa: <strong>${c.max_distance_km} km</strong></label>
                <input id="inp-max-dist" type="range" min="4" max="25" step="1" value="${c.max_distance_km}" class="form-control" />
              </div>

              <div class="form-group">
                <label>Hình thức làm việc</label>
                <select id="sel-work-mode" class="form-control">
                  <option value="Any" ${c.preferred_work_mode === "Any" ? "selected" : ""}>Tất cả (Onsite / Hybrid / Remote)</option>
                  <option value="Onsite" ${c.preferred_work_mode === "Onsite" ? "selected" : ""}>Chỉ Onsite tại văn phòng</option>
                  <option value="Hybrid" ${c.preferred_work_mode === "Hybrid" ? "selected" : ""}>Ưu tiên Hybrid linh hoạt</option>
                  <option value="Remote" ${c.preferred_work_mode === "Remote" ? "selected" : ""}>Remote từ xa</option>
                </select>
              </div>

              <div class="form-group">
                <label>Phạm vi Ngành tuyển dụng</label>
                <select id="sel-strict-major" class="form-control">
                  <option value="0" ${!c.strict_major_only ? "selected" : ""}>Mở rộng cả ngành gần / liên ngành</option>
                  <option value="1" ${c.strict_major_only ? "selected" : ""}>Chỉ lọc công việc đúng mã ngành</option>
                </select>
              </div>
            </div>

            <div style="margin-top:14px; display:flex; justify-content:space-between; align-items:center;">
              <span style="font-size:12px; color:var(--text-secondary);">
                Đang thỏa mãn: <strong>${state.dssResult.filter_report.strict_passed_count}</strong> / ${state.dssResult.filter_report.total_jobs} việc làm
              </span>
              <button id="btn-apply-profile" class="btn btn-primary">Cập nhật & Chạy Mô hình DSS →</button>
            </div>
          </div>
        </div>

        <!-- Cột phải: Quản lý Danh mục Kỹ năng & Mức độ thành thạo (1-5) -->
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">3. Hồ sơ Năng lực Kỹ năng của Sinh viên (${(s.skills || []).length} kỹ năng đang sở hữu)</div>
              <div class="panel-subtitle">Chọn mức độ thành thạo từ 1 (Cơ bản) đến 5 (Thành thạo cao) hoặc 0 để bỏ chọn kỹ năng</div>
            </div>
            <input
              id="inp-skill-search"
              class="form-control"
              style="width:230px;"
              placeholder="Tìm nhanh kỹ năng (VD: Python, PLC)..."
              value="${state.skillSearchText}"
            />
          </div>

          <div class="skill-category-tabs">
            ${categories
              .map(
                (cat) => `
              <button class="cat-pill ${state.activeSkillCategory === cat.key ? "active" : ""}" data-cat="${cat.key}">
                ${cat.label}
              </button>
            `
              )
              .join("")}
          </div>

          <div class="skills-grid">
            ${filteredSkills
              .map((sk) => {
                const curLv = stuSkillMap[sk.id] || 0;
                return `
                <div class="skill-item-card ${curLv > 0 ? "owned" : ""}">
                  <div>
                    <div class="skill-name-label">${sk.name}</div>
                    <div style="font-size:11px; color:var(--text-muted);">${sk.category}</div>
                  </div>
                  <div class="level-dots">
                    ${[0, 1, 2, 3, 4, 5]
                      .map(
                        (lv) => `
                      <button
                        class="lv-btn ${curLv === lv ? "active" : ""}"
                        data-skill-id="${sk.id}"
                        data-skill-lv="${lv}"
                        title="${lv === 0 ? "Chưa có kỹ năng này" : "Mức độ " + lv + "/5"}"
                      >${lv === 0 ? "×" : lv}</button>
                    `
                      )
                      .join("")}
                  </div>
                </div>
              `;
              })
              .join("")}
          </div>
        </div>
      </div>
    `;
  }

  function renderAhpTab() {
    const ahp = state.dssResult.ahp;
    const criteria = state.dssResult.criteria;
    const presets = Object.values(state.snapshot.ahp_presets);

    return `
      <div style="display:flex; flex-direction:column; gap:18px;">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">1. Chọn nhanh Cấu hình Tâm lý Ưu tiên của Sinh viên (AHP Presets)</div>
              <div class="panel-subtitle">Mỗi sinh viên có quan điểm đánh đổi khác nhau giữa Lương, Cơ hội học tập, Đúng chuyên ngành và Áp lực</div>
            </div>
            <span class="badge badge-purple">Phương pháp Thomas L. Saaty (1980)</span>
          </div>

          <div class="preset-cards">
            ${presets
              .map(
                (p) => `
              <div class="preset-card ${state.activeAhpPreset === p.key ? "active" : ""}" data-preset="${p.key}">
                <h4>${p.name}</h4>
                <p>${p.description}</p>
              </div>
            `
              )
              .join("")}
          </div>
        </div>

        <div class="grid-main-sidebar">
          <!-- Ma trận so sánh cặp 6x6 -->
          <div class="panel-card">
            <div class="panel-header">
              <div>
                <div class="panel-title">2. Ma trận So sánh Cặp Các Tiêu chí $A = [a_{ij}]_{6 \times 6}$</div>
                <div class="panel-subtitle">Điều chỉnh nửa tam giác trên (ô màu xanh nhạt); nửa dưới tự động cập nhật giá trị nghịch đảo $a_{ji} = 1 / a_{ij}$</div>
              </div>
              <button id="btn-test-inconsistent" class="btn btn-outline btn-sm" title="Thử tạo mâu thuẫn để kiểm tra cảnh báo CR >= 0.10">
                Thử tạo mâu thuẫn (Demo CR > 0.1)
              </button>
            </div>

            <div class="matrix-table-wrap">
              <table class="matrix-table">
                <thead>
                  <tr>
                    <th>Tiêu chí</th>
                    ${criteria.map((c) => `<th title="${c.name}">${c.code}: ${c.short_name}</th>`).join("")}
                  </tr>
                </thead>
                <tbody>
                  ${criteria
                    .map((rowCrit, i) => {
                      return `
                      <tr>
                        <th style="text-align:left;">${rowCrit.code}: ${rowCrit.short_name}</th>
                        ${criteria
                          .map((colCrit, j) => {
                            const val = ahp.pairwise_matrix[i][j];
                            if (i === j) {
                              return `<td class="diag-cell">1.00</td>`;
                            } else if (i < j) {
                              return `
                                <td class="upper-cell">
                                  <select class="saaty-select" data-row="${i}" data-col="${j}">
                                    ${SAATY_OPTIONS.map((opt) => {
                                      const isSelected = Math.abs(opt.val - val) < 0.035;
                                      return `<option value="${opt.val}" ${isSelected ? "selected" : ""}>${opt.label.split(" ")[0]}</option>`;
                                    }).join("")}
                                  </select>
                                </td>
                              `;
                            } else {
                              return `<td class="lower-cell">${Number(val).toFixed(3)}</td>`;
                            }
                          })
                          .join("")}
                      </tr>
                    `;
                    })
                    .join("")}
                </tbody>
              </table>
            </div>

            <div style="margin-top:16px;">
              <div style="font-weight:700; font-size:13px; margin-bottom:8px;">Ma trận Chuẩn hóa theo Cột & Vector Nhất quán ($\lambda_i = (Aw)_i / w_i$):</div>
              <div class="matrix-table-wrap">
                <table class="matrix-table">
                  <thead>
                    <tr>
                      <th>Tiêu chí</th>
                      ${criteria.map((c) => `<th>${c.code}</th>`).join("")}
                      <th>Trọng số $w_i$</th>
                      <th>$A \cdot w$</th>
                      <th>$\lambda_i$</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${criteria
                      .map(
                        (c, i) => `
                      <tr>
                        <th style="text-align:left;">${c.code} (${c.type})</th>
                        ${ahp.normalized_matrix[i].map((nv) => `<td>${Number(nv).toFixed(4)}</td>`).join("")}
                        <td style="font-weight:800; color:var(--primary);">${(ahp.weights[i] * 100).toFixed(2)}%</td>
                        <td>${ahp.weighted_sum_vector[i].toFixed(4)}</td>
                        <td>${ahp.consistency_vector[i].toFixed(4)}</td>
                      </tr>
                    `
                      )
                      .join("")}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Cột phải: Kiểm định CR & Trọng số -->
          <div style="display:flex; flex-direction:column; gap:16px;">
            <div class="panel-card">
              <div class="panel-header">
                <div>
                  <div class="panel-title">3. Kiểm định Tính Nhất quán (CR)</div>
                  <div class="panel-subtitle">Điều kiện chấp nhận ma trận Saaty: $CR < 0.10$</div>
                </div>
                <span class="badge ${ahp.is_consistent ? "badge-green" : "badge-red"}">
                  ${ahp.is_consistent ? "HỢP LỆ (CR < 10%)" : "MÂU THUẪN (CR ≥ 10%)"}
                </span>
              </div>

              <div class="formula-banner">
                λ_max = ${ahp.lambda_max.toFixed(4)} &nbsp;|&nbsp; n = ${ahp.n}<br/>
                CI = (λ_max - n)/(n - 1) = ${ahp.ci.toFixed(4)}<br/>
                RI (n=6) = ${ahp.ri.toFixed(2)} &nbsp;⇒&nbsp; <strong>CR = CI / RI = ${(ahp.cr * 100).toFixed(2)}%</strong>
              </div>

              ${
                !ahp.is_consistent && ahp.inconsistency_hints.length > 0
                  ? `
                <div style="background:var(--danger-soft); border:1px solid #fca5a5; padding:12px; border-radius:10px; margin-bottom:12px;">
                  <div style="font-weight:700; color:var(--danger); margin-bottom:6px;">
                    Phát hiện cặp đánh giá thiếu tính bắc cầu:
                  </div>
                  ${ahp.inconsistency_hints
                    .map(
                      (h) => `
                    <div style="font-size:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; gap:8px;">
                      <span>• ${h.message}</span>
                      <button class="btn btn-primary btn-sm btn-fix-ahp" data-row="${h.row_index}" data-col="${h.col_index}" data-val="${h.suggested_value}">
                        Sửa thành ${h.suggested_value}
                      </button>
                    </div>
                  `
                    )
                    .join("")}
                </div>
              `
                  : `
                <div style="background:var(--success-soft); border:1px solid #86efac; padding:11px 14px; border-radius:10px; font-size:12.5px; color:var(--success);">
                  ✓ Ma trận so sánh cặp hoàn toàn nhất quán (${(ahp.cr * 100).toFixed(2)}% &lt; 10%). Trọng số đủ độ tin cậy đưa vào mô hình TOPSIS.
                </div>
              `
              }
            </div>

            <div class="panel-card">
              <div class="panel-header">
                <div>
                  <div class="panel-title">4. Vector Trọng số Ưu tiên ($W$)</div>
                  <div class="panel-subtitle">Đầu vào trực tiếp cho bước chuẩn hóa có trọng số của TOPSIS</div>
                </div>
              </div>

              ${criteria
                .map((c, i) => {
                  const pct = (ahp.weights[i] * 100).toFixed(1);
                  return `
                  <div class="weight-bar-row">
                    <div class="weight-bar-header">
                      <span>${c.code}: ${c.name} <small style="color:var(--text-muted);">(${c.type})</small></span>
                      <span style="color:var(--primary); font-weight:800;">${pct}%</span>
                    </div>
                    <div class="weight-bar-track">
                      <div class="weight-bar-fill" style="width:${Math.min(100, pct * 2.2)}%;"></div>
                    </div>
                  </div>
                `;
                })
                .join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function renderDashboardTab() {
    const res = state.dssResult;
    const jobs = res.ranked_jobs || [];
    const selectedJob = jobs.find((j) => j.id === state.selectedJobId) || jobs[0];
    const top1Job = jobs[0];
    const sa = selectedJob ? selectedJob.evaluation.skill_analysis : null;

    return `
      <div class="grid-main-sidebar">
        <!-- Cột trái: Danh sách Xếp hạng Việc làm TOPSIS -->
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Bảng Xếp hạng Khuyến nghị Việc làm theo Mô hình Hybrid AHP - TOPSIS</div>
              <div class="panel-subtitle">
                Đã đánh giá <strong>${res.filter_report.evaluated_pool_count}</strong> vị trí phù hợp nhất cho <strong>${res.student.full_name}</strong>
                ${
                  res.filter_report.relaxation_applied
                    ? `<span class="badge badge-amber" style="margin-left:6px;">Đã nới lỏng mềm ràng buộc để đủ tập phương án</span>`
                    : ""
                }
              </div>
            </div>
            <button id="btn-goto-math" class="btn btn-outline btn-sm">Xem Ma trận Toán học →</button>
          </div>

          <div class="job-rank-list">
            ${jobs
              .slice(0, 15)
              .map((job) => {
                const rk = job.topsis.rank;
                const cv = job.evaluation.criteria_values;
                const isSel = selectedJob && job.id === selectedJob.id;
                const medalClass = rk <= 3 ? `rank-${rk}` : "";
                return `
                <div class="job-card ${isSel ? "selected" : ""}" data-job-id="${job.id}">
                  <div class="job-card-top">
                    <div class="rank-medal ${medalClass}">#${rk}</div>
                    <div class="job-title-group">
                      <h3>${job.title}</h3>
                      <div class="job-meta-line">
                        <span class="badge badge-blue">${job.company_short} (★${job.company_rating})</span>
                        <span class="badge badge-purple">${job.level}</span>
                        <span class="badge badge-green">${job.work_mode}</span>
                        <span>📍 ${job.district} (~${job.distance_km_from_center} km)</span>
                        <span>💰 Dải lương: ${job.salary_min} - ${job.salary_max} triệu</span>
                      </div>
                    </div>
                    <div class="score-box">
                      <div class="c-star-pill">C* = ${job.topsis.c_star.toFixed(4)}</div>
                      <div class="c-star-sub">Độ khớp lý tưởng: <strong>${job.topsis.match_percentage}%</strong></div>
                      <div class="c-star-sub">Hạng SAW đối chứng: #${job.topsis.saw_rank}</div>
                    </div>
                  </div>

                  <div class="criteria-mini-grid">
                    <div class="crit-mini-cell">
                      <div class="c-code">C1: Kỹ năng</div>
                      <div class="c-val" style="color:var(--primary);">${cv.C1}%</div>
                    </div>
                    <div class="crit-mini-cell">
                      <div class="c-code">C2: Lương dự kiến</div>
                      <div class="c-val" style="color:var(--success);">${cv.C2} tr</div>
                    </div>
                    <div class="crit-mini-cell">
                      <div class="c-code">C3: Độ hợp Hồ sơ</div>
                      <div class="c-val">${cv.C3}/10</div>
                    </div>
                    <div class="crit-mini-cell">
                      <div class="c-code">C4: Đào tạo</div>
                      <div class="c-val">${cv.C4}/10</div>
                    </div>
                    <div class="crit-mini-cell">
                      <div class="c-code">C5: Phúc lợi</div>
                      <div class="c-val">${cv.C5}/10</div>
                    </div>
                    <div class="crit-mini-cell">
                      <div class="c-code">C6: Áp lực/Đi lại</div>
                      <div class="c-val" style="color:var(--warning);">${cv.C6}/10</div>
                    </div>
                  </div>
                </div>
              `;
              })
              .join("")}
          </div>
        </div>

        <!-- Cột phải: Phân tích sâu Phương án đang chọn (Radar Chart + Giải thích + Skill Gap) -->
        <div style="display:flex; flex-direction:column; gap:16px;">
          ${
            selectedJob
              ? `
            <div class="panel-card">
              <div class="panel-header">
                <div>
                  <div class="panel-title">Phân tích Đa chiều: Hạng #${selectedJob.topsis.rank} — ${selectedJob.company_short}</div>
                  <div class="panel-subtitle">${selectedJob.title} (${selectedJob.job_code})</div>
                </div>
                <span class="badge badge-blue">C* = ${selectedJob.topsis.c_star.toFixed(4)}</span>
              </div>

              ${buildRadarChartSVG(selectedJob, top1Job)}

              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px;">
                <div style="background:var(--success-soft); padding:10px; border-radius:8px; text-align:center;">
                  <div style="font-size:11px; color:var(--text-secondary);">Khoảng cách tới Lý tưởng Tốt ($D_i^+$)</div>
                  <div style="font-size:16px; font-weight:800; color:var(--success);">${selectedJob.topsis.d_plus.toFixed(4)}</div>
                  <div style="font-size:11px; color:var(--text-muted);">(Càng nhỏ càng tốt)</div>
                </div>
                <div style="background:var(--primary-soft); padding:10px; border-radius:8px; text-align:center;">
                  <div style="font-size:11px; color:var(--text-secondary);">Khoảng cách tới Lý tưởng Xấu ($D_i^-$)</div>
                  <div style="font-size:16px; font-weight:800; color:var(--primary);">${selectedJob.topsis.d_minus.toFixed(4)}</div>
                  <div style="font-size:11px; color:var(--text-muted);">(Càng lớn càng tốt)</div>
                </div>
              </div>

              <div class="explanation-box">
                <div style="font-weight:700; margin-bottom:6px; color:var(--text-main);">Giải thích Khuyến nghị từ Hệ Trợ Giúp Quyết Định:</div>
                <ul>
                  ${selectedJob.decision_explanation.strengths
                    .map((st) => `<li style="color:var(--success);">✓ ${st}</li>`)
                    .join("")}
                  ${selectedJob.decision_explanation.warnings
                    .map((w) => `<li style="color:var(--warning);">⚠ ${w}</li>`)
                    .join("")}
                </ul>
              </div>
            </div>

            <div class="panel-card">
              <div class="panel-header">
                <div>
                  <div class="panel-title">Đối chiếu Kỹ năng Công việc Yêu cầu (${sa.matched_count}/${sa.total_required} đạt chuẩn)</div>
                  <div class="panel-subtitle">Yêu cầu tối thiểu: GPA ≥ ${selectedJob.min_gpa} | Ngoại ngữ bậc ${selectedJob.min_english_tier} | KN ≥ ${selectedJob.min_exp_months} tháng</div>
                </div>
              </div>

              <div style="display:flex; flex-direction:column; gap:8px;">
                ${sa.matched_skills
                  .map(
                    (sk) => `
                  <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; background:var(--success-soft); border-radius:7px; font-size:12.5px;">
                    <span><strong>✓ ${sk.skill_name}</strong> ${sk.is_mandatory ? '<span class="badge badge-red">Bắt buộc</span>' : ""}</span>
                    <span style="font-weight:700; color:var(--success);">SV: ${sk.student_level}/5 (YC: ${sk.required_level}/5)</span>
                  </div>
                `
                  )
                  .join("")}

                ${sa.partial_skills
                  .map(
                    (sk) => `
                  <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; background:var(--warning-soft); border-radius:7px; font-size:12.5px;">
                    <span><strong>◐ ${sk.skill_name}</strong> (Cần nâng cấp +${sk.gap} bậc)</span>
                    <span style="font-weight:700; color:var(--warning);">SV: ${sk.student_level}/5 (YC: ${sk.required_level}/5)</span>
                  </div>
                `
                  )
                  .join("")}

                ${sa.missing_skills
                  .map(
                    (sk) => `
                  <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; background:var(--danger-soft); border-radius:7px; font-size:12.5px;">
                    <span><strong>✗ ${sk.skill_name}</strong> ${sk.is_mandatory ? '<span class="badge badge-red">Bắt buộc</span>' : ""}</span>
                    <span style="font-weight:700; color:var(--danger);">Chưa có (YC: ${sk.required_level}/5)</span>
                  </div>
                `
                  )
                  .join("")}
              </div>
            </div>
          `
              : ""
          }
        </div>
      </div>
    `;
  }

  function renderMathTab() {
    const m = state.dssResult.topsis_matrices;
    const rows = m.inspector_rows || [];
    const codes = m.criteria_codes || ["C1", "C2", "C3", "C4", "C5", "C6"];

    return `
      <div style="display:flex; flex-direction:column; gap:18px;">
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Giải trình Từng bước Tính toán Mô hình Toán học TOPSIS & Đối chứng SAW (White-box Inspector)</div>
              <div class="panel-subtitle">Hiển thị minh bạch các ma trận trung gian phục vụ kiểm chứng kết quả và bảo vệ báo cáo giữa kỳ / cuối kỳ</div>
            </div>
            <span class="badge badge-blue">Top 15 Phương án Khả thi</span>
          </div>

          <div class="formula-banner">
            • Bước 1 (Chuẩn hóa Vector Euclid): r_ij = x_ij / sqrt(Σ x_kj²) &nbsp;&nbsp;|&nbsp;&nbsp;
            • Bước 2 (Nhân trọng số AHP): v_ij = w_j × r_ij<br/>
            • Bước 3 (Giải pháp Lý tưởng): A+ = {max v_ij (j ∈ Benefit), min v_ij (j ∈ Cost)} &nbsp;&nbsp;|&nbsp;&nbsp;
            • Bước 4 (Độ đo tương tự): C_i* = D_i- / (D_i+ + D_i-)
          </div>

          <!-- Bảng 1: Vector Chuẩn Euclid, Trọng số W, Giải pháp Lý tưởng A+ và A- -->
          <div style="font-weight:700; margin-bottom:8px;">1. Thông số Chuẩn hóa Cột, Trọng số AHP ($w_j$) và Giải pháp Lý tưởng ($A^+, A^-$):</div>
          <div class="matrix-table-wrap" style="margin-bottom:18px;">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th>Tham số hệ thống</th>
                  ${codes.map((c, idx) => `<th>${c} (${m.criteria_types[idx]})</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th style="text-align:left;">Mẫu số chuẩn Euclid $\sqrt{\sum x_{ij}^2}$</th>
                  ${m.column_norms.map((v) => `<td>${Number(v).toFixed(4)}</td>`).join("")}
                </tr>
                <tr>
                  <th style="text-align:left;">Trọng số AHP ($w_j$)</th>
                  ${m.weights.map((w) => `<td style="font-weight:800; color:var(--primary);">${Number(w).toFixed(4)}</td>`).join("")}
                </tr>
                <tr>
                  <th style="text-align:left; color:var(--success);">Giải pháp Lý tưởng Tốt ($A^+$)</th>
                  ${m.ideal_best.map((v) => `<td style="background:var(--success-soft); font-weight:700; color:var(--success);">${Number(v).toFixed(5)}</td>`).join("")}
                </tr>
                <tr>
                  <th style="text-align:left; color:var(--danger);">Giải pháp Lý tưởng Xấu ($A^-$)</th>
                  ${m.ideal_worst.map((v) => `<td style="background:var(--danger-soft); font-weight:700; color:var(--danger);">${Number(v).toFixed(5)}</td>`).join("")}
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Bảng 2: Ma trận Quyết định Gốc X = [x_ij] -->
          <div style="font-weight:700; margin-bottom:8px;">2. Ma trận Quyết định Gốc $X = [x_{ij}]$ và Kết quả Xếp hạng $D_i^+, D_i^-, C_i^*$ (Đối chiếu SAW):</div>
          <div class="matrix-table-wrap" style="margin-bottom:18px;">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th>Hạng TOPSIS</th>
                  <th>Mã CV</th>
                  <th>Vị trí Tuyển dụng & Doanh nghiệp</th>
                  ${codes.map((c) => `<th>${c} (Gốc)</th>`).join("")}
                  <th>$D_i^+$</th>
                  <th>$D_i^-$</th>
                  <th>$C_i^*$ (TOPSIS)</th>
                  <th>Điểm SAW</th>
                  <th>Hạng SAW</th>
                </tr>
              </thead>
              <tbody>
                ${rows
                  .map(
                    (r) => `
                  <tr>
                    <td style="font-weight:800;">#${r.rank}</td>
                    <td><code>${r.job_code}</code></td>
                    <td style="text-align:left; font-weight:600;">${r.title}</td>
                    ${r.raw.map((v) => `<td>${Number(v).toFixed(2)}</td>`).join("")}
                    <td style="color:var(--danger);">${r.d_plus.toFixed(4)}</td>
                    <td style="color:var(--success);">${r.d_minus.toFixed(4)}</td>
                    <td style="font-weight:800; color:var(--primary); background:var(--primary-soft);">${r.c_star.toFixed(4)}</td>
                    <td>${r.saw_score.toFixed(4)}</td>
                    <td>#${r.saw_rank}</td>
                  </tr>
                `
                  )
                  .join("")}
              </tbody>
            </table>
          </div>

          <!-- Bảng 3: Ma trận Chuẩn hóa có Trọng số V = [v_ij] -->
          <div style="font-weight:700; margin-bottom:8px;">3. Ma trận Quyết định Chuẩn hóa có Trọng số $V = [v_{ij} = w_j \cdot r_{ij}]$:</div>
          <div class="matrix-table-wrap">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th>Hạng</th>
                  <th>Mã CV</th>
                  <th>Doanh nghiệp</th>
                  ${codes.map((c) => `<th>$v_{i,${c}}$</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                ${rows
                  .map(
                    (r) => `
                  <tr>
                    <td>#${r.rank}</td>
                    <td><code>${r.job_code}</code></td>
                    <td style="font-weight:600;">${r.company_short}</td>
                    ${r.weighted.map((v) => `<td>${Number(v).toFixed(4)}</td>`).join("")}
                  </tr>
                `
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  function renderWhatIfTab() {
    const roadmap = state.dssResult.skill_gap_roadmap || [];
    const wif = state.whatIfResult;
    const comparisons = wif ? wif.comparison : [];

    return `
      <div class="grid-sidebar-main">
        <!-- Cột trái: Lộ trình Bù đắp Kỹ năng & Thiết lập Kịch bản Giả định -->
        <div style="display:flex; flex-direction:column; gap:16px;">
          <div class="panel-card">
            <div class="panel-header">
              <div>
                <div class="panel-title">1. Lộ trình Kỹ năng Ưu tiên Bổ sung (Skill Gap Roadmap)</div>
                <div class="panel-subtitle">Tổng hợp các kỹ năng còn thiếu xuất hiện nhiều nhất trong Top 10 việc làm mục tiêu của bạn</div>
              </div>
              <span class="badge badge-purple">Gợi ý học tập</span>
            </div>

            <div style="display:flex; flex-direction:column; gap:10px;">
              ${roadmap
                .map((sk) => {
                  const isAdded = Boolean(state.whatIfAddedSkills[sk.skill_id]);
                  return `
                  <div style="border:1px solid ${
                    isAdded ? "#2563eb" : "var(--border-color)"
                  }; background:${
                    isAdded ? "var(--primary-soft)" : "var(--bg-subtle)"
                  }; padding:10px 12px; border-radius:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                      <div>
                        <div style="font-weight:700; font-size:13px;">${sk.skill_name}</div>
                        <div style="font-size:11.5px; color:var(--text-secondary);">
                          Xuất hiện ở <strong>${sk.appearances_in_top_jobs}/10</strong> việc làm Top đầu
                          ${
                            sk.mandatory_in_jobs > 0
                              ? `• <span style="color:var(--danger); font-weight:700;">Bắt buộc ở ${sk.mandatory_in_jobs} việc</span>`
                              : ""
                          }
                        </div>
                      </div>
                      <button
                        class="btn ${isAdded ? "btn-primary" : "btn-outline"} btn-sm btn-toggle-whatif-skill"
                        data-skill-id="${sk.skill_id}"
                        data-rec-lv="${sk.recommended_level}"
                      >
                        ${isAdded ? `✓ Đã giả định đạt ${state.whatIfAddedSkills[sk.skill_id]}/5` : `+ Giả định học lên ${sk.recommended_level}/5`}
                      </button>
                    </div>
                  </div>
                `;
                })
                .join("")}
            </div>
          </div>

          <div class="panel-card">
            <div class="panel-header">
              <div>
                <div class="panel-title">2. Giả định Cải thiện Ngoại ngữ & Thực tập</div>
                <div class="panel-subtitle">Xem thứ hạng thay đổi thế nào nếu nâng chứng chỉ tiếng Anh hoặc tích lũy thêm thực tập</div>
              </div>
            </div>

            <div class="form-grid">
              <div class="form-group full">
                <label>Trình độ Ngoại ngữ Giả định (Hiện tại: Bậc ${state.student.english_tier})</label>
                <select id="sel-whatif-eng" class="form-control">
                  ${ENGLISH_TIERS.map(
                    (e) => `
                    <option value="${e.tier}" ${
                      Number(state.whatIfEnglishTier || state.student.english_tier) === e.tier
                        ? "selected"
                        : ""
                    }>
                      ${e.label}
                    </option>
                  `
                  ).join("")}
                </select>
              </div>

              <div class="form-group full">
                <label>Số tháng Thực tập Giả định: <strong>${
                  state.whatIfInternMonths !== null
                    ? state.whatIfInternMonths
                    : state.student.internship_months
                } tháng</strong> (Hiện tại: ${state.student.internship_months} tháng)</label>
                <input
                  id="inp-whatif-exp"
                  type="range"
                  min="0"
                  max="18"
                  step="1"
                  value="${
                    state.whatIfInternMonths !== null
                      ? state.whatIfInternMonths
                      : state.student.internship_months
                  }"
                  class="form-control"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Cột phải: Kết quả Phân tích Độ nhạy (Trước & Sau Mô phỏng) -->
        <div class="panel-card">
          <div class="panel-header">
            <div>
              <div class="panel-title">Kết quả Phân tích Độ nhạy & Biến động Thứ hạng (What-If Simulation Results)</div>
              <div class="panel-subtitle">
                Đang mô phỏng bổ sung <strong>${Object.keys(state.whatIfAddedSkills).length} kỹ năng</strong> cho sinh viên <strong>${state.student.full_name}</strong>
              </div>
            </div>
            <button id="btn-reset-whatif" class="btn btn-outline btn-sm">Đặt lại kịch bản</button>
          </div>

          <div class="matrix-table-wrap">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th>Hạng Mới</th>
                  <th>Biến động Hạng</th>
                  <th>Vị trí Công việc & Doanh nghiệp</th>
                  <th>Điểm Kỹ năng $C_1$ (Cũ → Mới)</th>
                  <th>Lương Dự kiến $C_2$ (Cũ → Mới)</th>
                  <th>Hệ số $C_i^*$ (Cũ → Mới)</th>
                  <th>$\Delta C_i^*$</th>
                </tr>
              </thead>
              <tbody>
                ${comparisons
                  .map((row) => {
                    const rkDelta = row.rank_delta;
                    let deltaBadge = `<span class="badge" style="background:#f1f5f9; color:#64748b;">Giữ nguyên</span>`;
                    if (rkDelta > 0) {
                      deltaBadge = `<span class="badge badge-green">▲ Tăng ${rkDelta} bậc (từ #${row.old_rank})</span>`;
                    } else if (rkDelta < 0) {
                      deltaBadge = `<span class="badge badge-amber">▼ Giảm ${Math.abs(rkDelta)} bậc (từ #${row.old_rank})</span>`;
                    }
                    const cDelta = row.c_star_delta;
                    return `
                    <tr>
                      <td style="font-weight:800; font-size:14px;">#${row.new_rank}</td>
                      <td>${deltaBadge}</td>
                      <td style="text-align:left;">
                        <div style="font-weight:700;">${row.title}</div>
                        <div style="font-size:11.5px; color:var(--text-muted);">${row.company_short} • ${row.level} (${row.job_code})</div>
                      </td>
                      <td>
                        ${row.old_skill_score}% → <strong style="color:var(--primary);">${row.new_skill_score}%</strong>
                      </td>
                      <td>
                        ${row.old_salary} tr → <strong style="color:var(--success);">${row.new_salary} tr</strong>
                      </td>
                      <td>
                        ${row.old_c_star.toFixed(4)} → <strong>${row.new_c_star.toFixed(4)}</strong>
                      </td>
                      <td style="font-weight:700; color:${cDelta > 0 ? "var(--success)" : "var(--text-muted)"};">
                        ${cDelta >= 0 ? "+" : ""}${cDelta.toFixed(4)}
                      </td>
                    </tr>
                  `;
                  })
                  .join("")}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // MAIN RENDER & EVENT BINDING
  // =========================================================================
  function renderApp() {
    const root = document.getElementById("dss-app-root");
    if (!root || !state.dssResult) return;

    const res = state.dssResult;
    const top1 = res.ranked_jobs[0];
    const ahp = res.ahp;

    let tabContent = "";
    if (state.activeTab === "profile") tabContent = renderProfileTab();
    else if (state.activeTab === "ahp") tabContent = renderAhpTab();
    else if (state.activeTab === "dashboard") tabContent = renderDashboardTab();
    else if (state.activeTab === "math") tabContent = renderMathTab();
    else if (state.activeTab === "whatif") tabContent = renderWhatIfTab();

    root.innerHTML = `
      <!-- Header -->
      <header class="dss-header">
        <div class="header-inner">
          <div class="brand-group">
            <div class="brand-badge">HUST DSS</div>
            <div class="brand-title">
              <h1>Hệ Trợ Giúp Quyết Định Tìm Việc Làm Cho Sinh Viên Tốt Nghiệp</h1>
              <p>Mô hình Kết hợp Lọc Ràng buộc + Độ khớp Kỹ năng + AHP (Saaty) + TOPSIS • CSDL: ${state.snapshot.market_stats.total_jobs} Việc làm & ${state.snapshot.market_stats.total_companies} Doanh nghiệp</p>
            </div>
          </div>

          <div class="header-controls">
            <div class="profile-selector-wrap">
              <label for="header-student-select">Hồ sơ SV mẫu:</label>
              <select id="header-student-select" class="profile-select">
                ${state.snapshot.student_profiles
                  .map(
                    (sp) => `
                  <option value="${sp.id}" ${Number(sp.id) === state.selectedStudentId ? "selected" : ""}>
                    [${sp.major_code} - GPA ${sp.gpa}] ${sp.full_name}
                  </option>
                `
                  )
                  .join("")}
              </select>
            </div>

            <div class="status-pill" title="${
              state.apiConnected
                ? "Đang kết nối trực tiếp tới Python SQLite REST API (127.0.0.1:8000)"
                : "Đang chạy trực tiếp trên Snapshot CSDL SQLite tích hợp (153 việc làm)"
            }">
              <span class="status-dot"></span>
              <span>${state.apiConnected ? "SQLite API Live" : "SQLite Snapshot Ready"}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- KPI Summary Strip -->
      <section class="kpi-strip">
        <div class="kpi-card">
          <div class="kpi-label">Sinh viên đang tư vấn</div>
          <div class="kpi-value" style="font-size:15.5px;">${res.student.full_name}</div>
          <div class="kpi-sub">Ngành ${res.student.major_code} • GPA ${Number(res.student.gpa).toFixed(2)} • ${(res.student.skills || []).length} kỹ năng</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-label">Tỷ số Nhất quán AHP (CR)</div>
          <div class="kpi-value" style="color:${ahp.is_consistent ? "var(--success)" : "var(--danger)"};">
            ${(ahp.cr * 100).toFixed(2)}% ${ahp.is_consistent ? "✓" : "⚠"}
          </div>
          <div class="kpi-sub">λ_max = ${ahp.lambda_max.toFixed(3)} • CI = ${ahp.ci.toFixed(4)} (Ngưỡng &lt; 10%)</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-label">Số Phương án Việc làm Khả thi</div>
          <div class="kpi-value">${res.filter_report.evaluated_pool_count} <span style="font-size:13px; font-weight:500; color:var(--text-muted);">/ ${res.filter_report.total_jobs} việc làm</span></div>
          <div class="kpi-sub">Lương kỳ vọng ≥ ${state.constraints.min_expected_salary} triệu VNĐ</div>
        </div>

        <div class="kpi-card" style="border-left: 4px solid var(--primary);">
          <div class="kpi-label">Khuyến nghị Hạng #1 (TOPSIS)</div>
          <div class="kpi-value" style="font-size:15px; color:var(--primary);">${top1 ? top1.title : "N/A"}</div>
          <div class="kpi-sub">
            ${top1 ? `C* = <strong>${top1.topsis.c_star.toFixed(4)}</strong> • Lương ~${top1.evaluation.criteria_values.C2} triệu/tháng` : ""}
          </div>
        </div>
      </section>

      <!-- Navigation Tabs -->
      <nav class="nav-tabs-bar">
        <div class="nav-tabs">
          <button class="tab-btn ${state.activeTab === "profile" ? "active" : ""}" data-tab="profile">
            <span class="tab-step-num">1</span> Hồ sơ Năng lực & Ràng buộc
          </button>
          <button class="tab-btn ${state.activeTab === "ahp" ? "active" : ""}" data-tab="ahp">
            <span class="tab-step-num">2</span> Trọng số AHP (CR = ${(ahp.cr * 100).toFixed(1)}%)
          </button>
          <button class="tab-btn ${state.activeTab === "dashboard" ? "active" : ""}" data-tab="dashboard">
            <span class="tab-step-num">3</span> Xếp hạng TOPSIS & Giải thích
          </button>
          <button class="tab-btn ${state.activeTab === "math" ? "active" : ""}" data-tab="math">
            <span class="tab-step-num">4</span> Ma trận Toán học (X, R, V, A+, A-)
          </button>
          <button class="tab-btn ${state.activeTab === "whatif" ? "active" : ""}" data-tab="whatif">
            <span class="tab-step-num">5</span> Skill Gap & Phân tích Độ nhạy (What-If)
          </button>
        </div>
      </nav>

      <!-- Active Tab Content -->
      <main class="main-container">
        ${tabContent}
      </main>
    `;

    bindEvents();
  }

  function bindEvents() {
    // Chuyển đổi hồ sơ sinh viên mẫu trên Header
    const headerSelect = document.getElementById("header-student-select");
    if (headerSelect) {
      headerSelect.addEventListener("change", (e) => {
        selectStudentProfile(Number(e.target.value), true);
      });
    }

    // Chuyển đổi giữa 5 Tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.activeTab = btn.getAttribute("data-tab");
        renderApp();
      });
    });

    // Sự kiện trong Tab 1 (Profile & Constraints)
    const inpGpa = document.getElementById("inp-gpa");
    if (inpGpa) {
      inpGpa.addEventListener("input", (e) => {
        state.student.gpa = Number(e.target.value);
        renderApp();
      });
    }
    const inpExp = document.getElementById("inp-exp");
    if (inpExp) {
      inpExp.addEventListener("input", (e) => {
        state.student.internship_months = Number(e.target.value);
        renderApp();
      });
    }
    const selMajor = document.getElementById("sel-major");
    if (selMajor) {
      selMajor.addEventListener("change", (e) => {
        state.student.major_code = e.target.value;
        recomputeDSS().then(() => renderApp());
      });
    }
    const selEng = document.getElementById("sel-english");
    if (selEng) {
      selEng.addEventListener("change", (e) => {
        state.student.english_tier = Number(e.target.value);
        recomputeDSS().then(() => renderApp());
      });
    }
    const inpMinSal = document.getElementById("inp-min-sal");
    if (inpMinSal) {
      inpMinSal.addEventListener("input", (e) => {
        state.constraints.min_expected_salary = Number(e.target.value);
        renderApp();
      });
    }
    const inpMaxDist = document.getElementById("inp-max-dist");
    if (inpMaxDist) {
      inpMaxDist.addEventListener("input", (e) => {
        state.constraints.max_distance_km = Number(e.target.value);
        renderApp();
      });
    }
    const selWorkMode = document.getElementById("sel-work-mode");
    if (selWorkMode) {
      selWorkMode.addEventListener("change", (e) => {
        state.constraints.preferred_work_mode = e.target.value;
        recomputeDSS().then(() => renderApp());
      });
    }
    const selStrictMajor = document.getElementById("sel-strict-major");
    if (selStrictMajor) {
      selStrictMajor.addEventListener("change", (e) => {
        state.constraints.strict_major_only = e.target.value === "1";
        recomputeDSS().then(() => renderApp());
      });
    }
    const btnApplyProfile = document.getElementById("btn-apply-profile");
    if (btnApplyProfile) {
      btnApplyProfile.addEventListener("click", () => {
        const nameEl = document.getElementById("inp-student-name");
        const goalEl = document.getElementById("inp-goal");
        if (nameEl) state.student.full_name = nameEl.value;
        if (goalEl) state.student.career_goal = goalEl.value;
        recomputeDSS().then(() => {
          state.activeTab = "dashboard";
          renderApp();
        });
      });
    }

    // Lọc nhóm kỹ năng & tìm kiếm kỹ năng
    document.querySelectorAll(".cat-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        state.activeSkillCategory = pill.getAttribute("data-cat");
        renderApp();
      });
    });

    const skillSearch = document.getElementById("inp-skill-search");
    if (skillSearch) {
      skillSearch.addEventListener("input", (e) => {
        state.skillSearchText = e.target.value;
        renderApp();
        const el = document.getElementById("inp-skill-search");
        if (el) {
          el.focus();
          el.setSelectionRange(el.value.length, el.value.length);
        }
      });
    }

    // Chỉnh sửa mức độ thành thạo kỹ năng (0..5)
    document.querySelectorAll(".lv-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sid = Number(btn.getAttribute("data-skill-id"));
        const lv = Number(btn.getAttribute("data-skill-lv"));
        const skillsArr = state.student.skills || [];
        const existingIdx = skillsArr.findIndex((s) => Number(s.skill_id) === sid);
        if (lv === 0) {
          if (existingIdx >= 0) skillsArr.splice(existingIdx, 1);
        } else {
          if (existingIdx >= 0) {
            skillsArr[existingIdx].proficiency_level = lv;
          } else {
            const skMeta = state.snapshot.skills.find((k) => Number(k.id) === sid);
            skillsArr.push({
              skill_id: sid,
              proficiency_level: lv,
              skill_name: skMeta ? skMeta.name : "",
              category: skMeta ? skMeta.category : "",
            });
          }
        }
        state.student.skills = skillsArr;
        recomputeDSS().then(() => renderApp());
      });
    });

    // Sự kiện trong Tab 2 (AHP Presets & Matrix)
    document.querySelectorAll(".preset-card").forEach((card) => {
      card.addEventListener("click", () => {
        const key = card.getAttribute("data-preset");
        state.activeAhpPreset = key;
        state.ahpMatrix = clone(state.snapshot.ahp_presets[key].matrix);
        recomputeDSS().then(() => renderApp());
      });
    });

    document.querySelectorAll(".saaty-select").forEach((sel) => {
      sel.addEventListener("change", (e) => {
        const r = Number(sel.getAttribute("data-row"));
        const c = Number(sel.getAttribute("data-col"));
        const val = Number(e.target.value);
        state.ahpMatrix[r][c] = val;
        state.ahpMatrix[c][r] = 1.0 / val;
        recomputeDSS().then(() => renderApp());
      });
    });

    const btnTestInconsistent = document.getElementById("btn-test-inconsistent");
    if (btnTestInconsistent) {
      btnTestInconsistent.addEventListener("click", () => {
        // Đặt C1 = 7*C2, C2 = 5*C3 nhưng C1 = 1/6*C3 để minh họa vi phạm tính bắc cầu (CR > 0.25)
        state.ahpMatrix[0][1] = 7.0;
        state.ahpMatrix[1][0] = 1 / 7.0;
        state.ahpMatrix[1][2] = 5.0;
        state.ahpMatrix[2][1] = 1 / 5.0;
        state.ahpMatrix[0][2] = 0.1667;
        state.ahpMatrix[2][0] = 6.0;
        recomputeDSS().then(() => renderApp());
      });
    }

    document.querySelectorAll(".btn-fix-ahp").forEach((btn) => {
      btn.addEventListener("click", () => {
        const r = Number(btn.getAttribute("data-row"));
        const c = Number(btn.getAttribute("data-col"));
        const val = Number(btn.getAttribute("data-val"));
        state.ahpMatrix[r][c] = val;
        state.ahpMatrix[c][r] = 1.0 / val;
        recomputeDSS().then(() => renderApp());
      });
    });

    // Sự kiện trong Tab 3 (Dashboard)
    document.querySelectorAll(".job-card").forEach((card) => {
      card.addEventListener("click", () => {
        state.selectedJobId = Number(card.getAttribute("data-job-id"));
        renderApp();
      });
    });

    const btnGotoMath = document.getElementById("btn-goto-math");
    if (btnGotoMath) {
      btnGotoMath.addEventListener("click", () => {
        state.activeTab = "math";
        renderApp();
      });
    }

    // Sự kiện trong Tab 5 (What-If Simulator)
    document.querySelectorAll(".btn-toggle-whatif-skill").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sid = Number(btn.getAttribute("data-skill-id"));
        const recLv = Number(btn.getAttribute("data-rec-lv") || 4);
        if (state.whatIfAddedSkills[sid]) {
          delete state.whatIfAddedSkills[sid];
        } else {
          state.whatIfAddedSkills[sid] = recLv;
        }
        recomputeWhatIf().then(() => renderApp());
      });
    });

    const selWhatIfEng = document.getElementById("sel-whatif-eng");
    if (selWhatIfEng) {
      selWhatIfEng.addEventListener("change", (e) => {
        state.whatIfEnglishTier = Number(e.target.value);
        recomputeWhatIf().then(() => renderApp());
      });
    }

    const inpWhatIfExp = document.getElementById("inp-whatif-exp");
    if (inpWhatIfExp) {
      inpWhatIfExp.addEventListener("input", (e) => {
        state.whatIfInternMonths = Number(e.target.value);
        recomputeWhatIf().then(() => renderApp());
      });
    }

    const btnResetWhatIf = document.getElementById("btn-reset-whatif");
    if (btnResetWhatIf) {
      btnResetWhatIf.addEventListener("click", () => {
        state.whatIfAddedSkills = {};
        state.whatIfEnglishTier = state.student.english_tier;
        state.whatIfInternMonths = state.student.internship_months;
        recomputeWhatIf().then(() => renderApp());
      });
    }
  }

  document.addEventListener("DOMContentLoaded", checkBackendAndInit);
})();


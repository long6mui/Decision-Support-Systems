/**
 * Bộ xử lý Mô hình Toán học DSS phía Client & Kết nối API SQLite Backend
 * Đồng bộ 100% công thức toán học với backend/services/dss_engine.py
 */

(function () {
  const SAATY_RI_TABLE = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.9,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
  };

  const MAJOR_AFFINITY = {
    IT1: { IT1: 1.0, IT2: 0.92, DS1: 0.9, EE1: 0.65, EE2: 0.6, ME1: 0.5, EM1: 0.72, EM2: 0.55 },
    IT2: { IT2: 1.0, IT1: 0.92, DS1: 0.82, EM1: 0.78, EE1: 0.68, EE2: 0.6, ME1: 0.52, EM2: 0.58 },
    DS1: { DS1: 1.0, IT1: 0.92, IT2: 0.82, EM1: 0.8, EM2: 0.72, EE2: 0.62, EE1: 0.58, ME1: 0.5 },
    EE1: { EE1: 1.0, EE2: 0.85, IT2: 0.72, IT1: 0.68, ME1: 0.78, DS1: 0.58, EM1: 0.45, EM2: 0.4 },
    EE2: { EE2: 1.0, EE1: 0.85, ME1: 0.88, IT2: 0.65, IT1: 0.62, DS1: 0.6, EM1: 0.48, EM2: 0.45 },
    ME1: { ME1: 1.0, EE2: 0.88, EE1: 0.78, IT2: 0.55, IT1: 0.5, DS1: 0.48, EM2: 0.52, EM1: 0.45 },
    EM1: { EM1: 1.0, EM2: 0.88, IT2: 0.78, DS1: 0.8, IT1: 0.7, EE2: 0.45, EE1: 0.42, ME1: 0.4 },
    EM2: { EM2: 1.0, EM1: 0.88, DS1: 0.72, IT2: 0.6, IT1: 0.55, ME1: 0.5, EE2: 0.45, EE1: 0.4 },
  };

  function round(val, digits = 4) {
    const f = Math.pow(10, digits);
    return Math.round((Number(val) + Number.EPSILON) * f) / f;
  }

  function calculateAHP(matrixInput, criteriaCodes = ["C1", "C2", "C3", "C4", "C5", "C6"]) {
    const n = matrixInput.length;
    const A = matrixInput.map((row) => row.map((v) => Number(v)));

    for (let i = 0; i < n; i++) {
      A[i][i] = 1.0;
      for (let j = i + 1; j < n; j++) {
        const val = Math.max(1 / 9, Math.min(9.0, Number(A[i][j]) || 1.0));
        A[i][j] = val;
        A[j][i] = 1.0 / val;
      }
    }

    const colSums = Array(n).fill(0);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        colSums[j] += A[i][j];
      }
    }

    const normalizedMatrix = A.map((row) =>
      row.map((val, j) => (colSums[j] > 0 ? val / colSums[j] : 1 / n))
    );

    let weights = normalizedMatrix.map((row) => row.reduce((a, b) => a + b, 0) / n);
    const wSum = weights.reduce((a, b) => a + b, 0);
    weights = weights.map((w) => (wSum > 0 ? w / wSum : 1 / n));

    const weightedSumVector = A.map((row) =>
      row.reduce((sum, aij, j) => sum + aij * weights[j], 0)
    );
    const consistencyVector = weightedSumVector.map((ws, i) =>
      weights[i] > 0 ? ws / weights[i] : n
    );
    const lambdaMax = consistencyVector.reduce((a, b) => a + b, 0) / n;
    const ci = n > 1 ? (lambdaMax - n) / (n - 1) : 0.0;
    const ri = SAATY_RI_TABLE[n] || 1.24;
    const cr = ri > 0 ? ci / ri : 0.0;
    const isConsistent = cr < 0.1;

    const inconsistencyHints = [];
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const idealRatio = weights[j] > 0 ? weights[i] / weights[j] : 1.0;
        const actualRatio = A[i][j];
        const relError = Math.abs(Math.log(actualRatio) - Math.log(idealRatio));
        if (relError > 0.45) {
          const suggestedVal = round(Math.max(1 / 9, Math.min(9.0, idealRatio)), 2);
          inconsistencyHints.push({
            pair: `${criteriaCodes[i]} vs ${criteriaCodes[j]}`,
            row_index: i,
            col_index: j,
            current_value: round(actualRatio, 3),
            suggested_value: suggestedVal,
            deviation_score: round(relError, 3),
            message: `Cặp (${criteriaCodes[i]}, ${criteriaCodes[j]}) đang đặt ${round(actualRatio, 2)}, nên điều chỉnh gần ${suggestedVal} để giảm tỷ số CR.`,
          });
        }
      }
    }
    inconsistencyHints.sort((a, b) => b.deviation_score - a.deviation_score);

    const weightsMap = {};
    criteriaCodes.forEach((c, idx) => {
      weightsMap[c] = round(weights[idx], 4);
    });

    return {
      n,
      criteria_codes: criteriaCodes,
      pairwise_matrix: A.map((r) => r.map((v) => round(v, 4))),
      column_sums: colSums.map((v) => round(v, 4)),
      normalized_matrix: normalizedMatrix.map((r) => r.map((v) => round(v, 4))),
      weights: weights.map((w) => round(w, 4)),
      weights_map: weightsMap,
      weighted_sum_vector: weightedSumVector.map((v) => round(v, 4)),
      consistency_vector: consistencyVector.map((v) => round(v, 4)),
      lambda_max: round(lambdaMax, 4),
      ci: round(ci, 4),
      ri: round(ri, 4),
      cr: round(cr, 4),
      is_consistent: isConsistent,
      inconsistency_hints: inconsistencyHints.slice(0, 3),
    };
  }

  function evaluateJobForStudent(student, studentSkillMap, job) {
    const jobSkills = job.required_skills || [];
    let totalWeight = 0.0;
    let earnedWeight = 0.0;
    let mandatoryMissingCount = 0;

    const matchedSkills = [];
    const partialSkills = [];
    const missingSkills = [];

    for (const js of jobSkills) {
      const sId = Number(js.skill_id);
      const reqLv = Number(js.required_level);
      const impW = Number(js.importance_weight);
      const isMand = Boolean(js.is_mandatory);
      const stuLv = Number(studentSkillMap[sId] || 0);

      totalWeight += impW;
      if (stuLv >= reqLv) {
        const bonusRatio = Math.min(1.08, 1.0 + 0.04 * (stuLv - reqLv));
        earnedWeight += impW * bonusRatio;
        matchedSkills.push({
          skill_id: sId,
          skill_name: js.skill_name,
          category: js.skill_category,
          student_level: stuLv,
          required_level: reqLv,
          is_mandatory: isMand,
          importance_weight: impW,
          status: "MATCHED",
        });
      } else if (stuLv > 0) {
        const ratio = (stuLv / reqLv) * 0.85;
        earnedWeight += impW * ratio;
        partialSkills.push({
          skill_id: sId,
          skill_name: js.skill_name,
          category: js.skill_category,
          student_level: stuLv,
          required_level: reqLv,
          gap: reqLv - stuLv,
          is_mandatory: isMand,
          importance_weight: impW,
          status: "PARTIAL",
        });
      } else {
        if (isMand) mandatoryMissingCount += 1;
        missingSkills.push({
          skill_id: sId,
          skill_name: js.skill_name,
          category: js.skill_category,
          student_level: 0,
          required_level: reqLv,
          gap: reqLv,
          is_mandatory: isMand,
          importance_weight: impW,
          status: "MISSING",
        });
      }
    }

    const rawSkillScore = totalWeight > 0 ? (earnedWeight / totalWeight) * 100.0 : 50.0;
    const mandatoryPenalty = Math.pow(0.86, mandatoryMissingCount);
    const c1SkillMatch = round(Math.max(8.0, Math.min(100.0, rawSkillScore * mandatoryPenalty)), 2);

    const stuMajor = student.major_code || "IT1";
    const jobMajor = job.major_code || "IT1";
    const majorFit = ((MAJOR_AFFINITY[stuMajor] && MAJOR_AFFINITY[stuMajor][jobMajor]) || 0.55) * 10.0;

    const stuGpa = Number(student.gpa || 3.0);
    const reqGpa = Number(job.min_gpa || 2.5);
    const gpaFit =
      stuGpa >= reqGpa
        ? Math.min(10.0, 8.0 + (stuGpa - reqGpa) * 2.5)
        : Math.max(3.0, 8.0 - (reqGpa - stuGpa) * 6.0);

    const stuEng = Number(student.english_tier || 3);
    const reqEng = Number(job.min_english_tier || 3);
    const engFit =
      stuEng >= reqEng
        ? Math.min(10.0, 8.2 + (stuEng - reqEng) * 0.9)
        : Math.max(3.0, 8.2 - (reqEng - stuEng) * 2.2);

    const stuExp = Number(student.internship_months || 3);
    const reqExp = Number(job.min_exp_months || 0);
    const expFit =
      stuExp >= reqExp
        ? Math.min(10.0, 8.5 + Math.min(1.5, (stuExp - reqExp) * 0.25))
        : Math.max(3.5, 8.5 - (reqExp - stuExp) * 0.8);

    const c3AcademicFit = round(0.4 * majorFit + 0.25 * gpaFit + 0.2 * engFit + 0.15 * expFit, 2);

    const salMin = Number(job.salary_min);
    const salMax = Number(job.salary_max);
    const compFactor = Math.min(1.0, Math.max(0.0, 0.65 * (c1SkillMatch / 100.0) + 0.35 * (c3AcademicFit / 10.0)));
    const c2ExpectedSalary = round(salMin + (salMax - salMin) * compFactor, 2);

    const levelBonus =
      stuExp <= 4 && (job.level === "Fresher" || job.level === "Management Trainee") ? 0.3 : 0.0;
    const c4Growth = round(Math.min(10.0, Math.max(1.0, Number(job.training_score) + levelBonus)), 2);

    const compRating10 = Number(job.company_rating || 4.2) * 2.0;
    const c5Welfare = round(Math.min(10.0, Math.max(1.0, 0.7 * Number(job.welfare_score) + 0.3 * compRating10)), 2);

    const rawDist = Number(job.distance_km_from_center || 8.0);
    const effDist =
      job.work_mode === "Remote" ? rawDist * 0.25 : job.work_mode === "Hybrid" ? rawDist * 0.65 : rawDist;
    const distCost10 = Math.min(10.0, Math.max(1.0, effDist / 2.0));
    const c6Cost = round(0.45 * distCost10 + 0.55 * Number(job.overtime_pressure_score), 2);

    return {
      criteria_values: {
        C1: c1SkillMatch,
        C2: c2ExpectedSalary,
        C3: c3AcademicFit,
        C4: c4Growth,
        C5: c5Welfare,
        C6: c6Cost,
      },
      skill_analysis: {
        matched_count: matchedSkills.length,
        partial_count: partialSkills.length,
        missing_count: missingSkills.length,
        total_required: jobSkills.length,
        mandatory_missing_count: mandatoryMissingCount,
        matched_skills: matchedSkills,
        partial_skills: partialSkills,
        missing_skills: missingSkills,
      },
      academic_breakdown: {
        major_fit: round(majorFit, 2),
        gpa_fit: round(gpaFit, 2),
        english_fit: round(engFit, 2),
        experience_fit: round(expFit, 2),
      },
    };
  }

  function buildDecisionExplanation(jobItem) {
    const cv = jobItem.evaluation.criteria_values;
    const sa = jobItem.evaluation.skill_analysis;
    const strengths = [];
    const warnings = [];

    if (cv.C1 >= 80) {
      strengths.push(`Độ khớp kỹ năng rất cao (${cv.C1}%), đáp ứng ${sa.matched_count}/${sa.total_required} kỹ năng.`);
    } else if (cv.C1 >= 60) {
      strengths.push(`Đáp ứng tốt nền tảng kỹ năng (${cv.C1}%), có thể bắt nhịp nhanh.`);
    } else {
      warnings.push(`Độ khớp kỹ năng hiện tại đạt ${cv.C1}%, cần bổ sung thêm ${sa.missing_count + sa.partial_count} kỹ năng.`);
    }

    if (cv.C2 >= 16.0) {
      strengths.push(`Mức thu nhập kỳ vọng hấp dẫn (~${cv.C2} triệu VNĐ/tháng).`);
    } else if (cv.C2 >= 12.0) {
      strengths.push(`Thu nhập khởi điểm khá tốt (~${cv.C2} triệu VNĐ/tháng).`);
    }

    if (cv.C4 >= 8.5) {
      strengths.push(`Chương trình đào tạo & Mentorship xuất sắc (${cv.C4}/10).`);
    }
    if (cv.C5 >= 8.4) {
      strengths.push(`Môi trường làm việc & đãi ngộ doanh nghiệp uy tín (${cv.C5}/10).`);
    }
    if (cv.C6 <= 4.8) {
      strengths.push(`Chi phí đi lại & áp lực OT thấp (${cv.C6}/10 - ${jobItem.work_mode}).`);
    } else if (cv.C6 >= 7.0) {
      warnings.push(`Áp lực công việc hoặc khoảng cách di chuyển khá cao (${cv.C6}/10).`);
    }
    if (sa.mandatory_missing_count > 0) {
      const names = sa.missing_skills.filter((s) => s.is_mandatory).map((s) => s.skill_name);
      warnings.push(`Cần ưu tiên học gấp kỹ năng bắt buộc: ${names.join(", ")}.`);
    }
    return { strengths, warnings };
  }

  function runTOPSIS(evaluatedJobs, weights, criteriaTypes, criteriaCodes) {
    const m = evaluatedJobs.length;
    const n = criteriaCodes.length;
    if (m === 0) return { ranked_jobs: [], matrices: {} };

    const X = evaluatedJobs.map((item) =>
      criteriaCodes.map((code) => Number(item.evaluation.criteria_values[code]))
    );

    const colNorms = Array(n).fill(0);
    for (let j = 0; j < n; j++) {
      let sq = 0;
      for (let i = 0; i < m; i++) sq += X[i][j] * X[i][j];
      colNorms[j] = Math.sqrt(sq);
    }

    const R = X.map((row) =>
      row.map((val, j) => (colNorms[j] > 0 ? val / colNorms[j] : 0))
    );

    const wSum = weights.reduce((a, b) => a + b, 0) || 1;
    const W = weights.map((w) => w / wSum);

    const V = R.map((row) => row.map((rVal, j) => rVal * W[j]));

    const idealBest = Array(n).fill(0);
    const idealWorst = Array(n).fill(0);
    for (let j = 0; j < n; j++) {
      const colVals = V.map((r) => r[j]);
      if (criteriaTypes[j] === "BENEFIT") {
        idealBest[j] = Math.max(...colVals);
        idealWorst[j] = Math.min(...colVals);
      } else {
        idealBest[j] = Math.min(...colVals);
        idealWorst[j] = Math.max(...colVals);
      }
    }

    const dPlus = V.map((row) =>
      Math.sqrt(row.reduce((acc, v, j) => acc + Math.pow(v - idealBest[j], 2), 0))
    );
    const dMinus = V.map((row) =>
      Math.sqrt(row.reduce((acc, v, j) => acc + Math.pow(v - idealWorst[j], 2), 0))
    );
    const cStar = dPlus.map((dp, i) => (dp + dMinus[i] > 0 ? dMinus[i] / (dp + dMinus[i]) : 0.5));

    // SAW calculation
    const sawScores = Array(m).fill(0);
    for (let j = 0; j < n; j++) {
      const colVals = X.map((r) => r[j]);
      const cMin = Math.min(...colVals);
      const cMax = Math.max(...colVals);
      for (let i = 0; i < m; i++) {
        let norm = 1.0;
        if (cMax > cMin) {
          norm =
            criteriaTypes[j] === "BENEFIT"
              ? (X[i][j] - cMin) / (cMax - cMin)
              : (cMax - X[i][j]) / (cMax - cMin);
        }
        sawScores[i] += W[j] * norm;
      }
    }

    const sawOrder = sawScores
      .map((s, idx) => ({ s, idx }))
      .sort((a, b) => b.s - a.s);
    const sawRankMap = {};
    sawOrder.forEach((item, rk) => {
      sawRankMap[item.idx] = rk + 1;
    });

    const enriched = evaluatedJobs.map((item, i) => {
      const copy = Object.assign({}, item);
      copy.topsis = {
        d_plus: round(dPlus[i], 5),
        d_minus: round(dMinus[i], 5),
        c_star: round(cStar[i], 5),
        match_percentage: round(cStar[i] * 100, 2),
        saw_score: round(sawScores[i], 5),
        saw_rank: sawRankMap[i],
        raw_vector: X[i].map((v) => round(v, 3)),
        normalized_vector: R[i].map((v) => round(v, 4)),
        weighted_vector: V[i].map((v) => round(v, 4)),
      };
      return copy;
    });

    enriched.sort((a, b) => b.topsis.c_star - a.topsis.c_star);
    enriched.forEach((item, idx) => {
      item.topsis.rank = idx + 1;
      item.decision_explanation = buildDecisionExplanation(item);
    });

    const inspectorRows = enriched.slice(0, 15).map((item) => ({
      job_id: item.id,
      job_code: item.job_code,
      title: item.title,
      company_short: item.company_short,
      rank: item.topsis.rank,
      saw_rank: item.topsis.saw_rank,
      raw: item.topsis.raw_vector,
      normalized: item.topsis.normalized_vector,
      weighted: item.topsis.weighted_vector,
      d_plus: item.topsis.d_plus,
      d_minus: item.topsis.d_minus,
      c_star: item.topsis.c_star,
      saw_score: item.topsis.saw_score,
    }));

    return {
      ranked_jobs: enriched,
      matrices: {
        criteria_codes: criteriaCodes,
        criteria_types: criteriaTypes,
        weights: W.map((w) => round(w, 4)),
        column_norms: colNorms.map((cn) => round(cn, 4)),
        ideal_best: idealBest.map((v) => round(v, 5)),
        ideal_worst: idealWorst.map((v) => round(v, 5)),
        inspector_rows: inspectorRows,
      },
    };
  }

  function runPipelineLocal(snapshot, payload) {
    const criteriaRows = snapshot.criteria;
    const criteriaCodes = criteriaRows.map((c) => c.code);
    const criteriaTypes = criteriaRows.map((c) => c.type);

    let student = payload.student;
    if (!student && payload.student_id) {
      student = snapshot.student_profiles.find((s) => Number(s.id) === Number(payload.student_id));
    }
    if (!student) student = snapshot.student_profiles[0];

    const studentSkillMap = {};
    (student.skills || []).forEach((s) => {
      studentSkillMap[Number(s.skill_id)] = Number(s.proficiency_level);
    });

    const presetKey = payload.ahp_preset || student.persona_preset || "balanced";
    const ahpMatrix =
      payload.ahp_matrix ||
      (snapshot.ahp_presets[presetKey] || snapshot.ahp_presets.balanced).matrix;
    const ahpResult = calculateAHP(ahpMatrix, criteriaCodes);

    let activeWeights = ahpResult.weights;
    if (payload.direct_weights && payload.direct_weights.length === criteriaCodes.length) {
      const s = payload.direct_weights.reduce((a, b) => a + Number(b), 0);
      if (s > 0) activeWeights = payload.direct_weights.map((x) => Number(x) / s);
    }

    const constraints = payload.constraints || {};
    const minSalary = Number(
      constraints.min_expected_salary !== undefined
        ? constraints.min_expected_salary
        : student.min_expected_salary || 0
    );
    const maxDistance = Number(
      constraints.max_distance_km !== undefined
        ? constraints.max_distance_km
        : student.max_distance_km || 25
    );
    const prefMode =
      constraints.preferred_work_mode !== undefined
        ? constraints.preferred_work_mode
        : student.preferred_work_mode || "Any";
    const allowedLevels = constraints.levels || ["Intern", "Fresher", "Junior", "Management Trainee"];
    const strictMajorOnly = Boolean(constraints.strict_major_only);
    const stuMajor = student.major_code || "IT1";

    const strictPassed = [];
    const relaxedCandidates = [];
    const rejectionStats = {
      total_jobs: snapshot.jobs.length,
      rejected_by_salary: 0,
      rejected_by_distance: 0,
      rejected_by_work_mode: 0,
      rejected_by_major: 0,
      rejected_by_level: 0,
    };

    for (const job of snapshot.jobs) {
      const evalRes = evaluateJobForStudent(student, studentSkillMap, job);
      const jobWithEval = Object.assign({}, job, { evaluation: evalRes });

      const affinity = (MAJOR_AFFINITY[stuMajor] && MAJOR_AFFINITY[stuMajor][job.major_code]) || 0.5;
      const minAffinity = strictMajorOnly ? 0.9 : 0.58;
      if (affinity < minAffinity) {
        rejectionStats.rejected_by_major += 1;
        continue;
      }
      if (allowedLevels.length > 0 && !allowedLevels.includes(job.level)) {
        rejectionStats.rejected_by_level += 1;
        continue;
      }

      const salaryOk = Number(job.salary_max) >= minSalary;
      if (!salaryOk) rejectionStats.rejected_by_salary += 1;

      const effDist =
        job.work_mode === "Remote"
          ? 0
          : job.work_mode === "Hybrid"
          ? Number(job.distance_km_from_center) * 0.7
          : Number(job.distance_km_from_center);
      const distanceOk = effDist <= maxDistance;
      if (!distanceOk) rejectionStats.rejected_by_distance += 1;

      const modeOk = !prefMode || prefMode === "Any" || job.work_mode === prefMode;
      if (!modeOk) rejectionStats.rejected_by_work_mode += 1;

      jobWithEval.constraint_check = {
        salary_ok: salaryOk,
        distance_ok: distanceOk,
        work_mode_ok: modeOk,
        all_strict_passed: Boolean(salaryOk && distanceOk && modeOk),
      };

      if (salaryOk && distanceOk && modeOk) {
        strictPassed.push(jobWithEval);
      } else {
        relaxedCandidates.push(jobWithEval);
      }
    }

    let relaxationApplied = false;
    const finalPool = [...strictPassed];
    if (finalPool.length < 10 && relaxedCandidates.length > 0) {
      relaxationApplied = true;
      relaxedCandidates.sort(
        (a, b) => b.evaluation.criteria_values.C1 - a.evaluation.criteria_values.C1
      );
      finalPool.push(...relaxedCandidates.slice(0, 12 - finalPool.length));
    }

    const topsisRes = runTOPSIS(finalPool, activeWeights, criteriaTypes, criteriaCodes);
    const rankedJobs = topsisRes.ranked_jobs;

    // Aggregate Skill Gap Roadmap
    const skillImpact = {};
    for (const job of rankedJobs.slice(0, 10)) {
      const sa = job.evaluation.skill_analysis;
      for (const sk of [...sa.missing_skills, ...sa.partial_skills]) {
        const sid = sk.skill_id;
        if (!skillImpact[sid]) {
          skillImpact[sid] = {
            skill_id: sid,
            skill_name: sk.skill_name,
            category: sk.category,
            current_level: sk.student_level,
            recommended_level: sk.required_level,
            appearances_in_top_jobs: 0,
            mandatory_in_jobs: 0,
            total_importance: 0.0,
            affected_jobs: [],
          };
        }
        const entry = skillImpact[sid];
        entry.appearances_in_top_jobs += 1;
        if (sk.is_mandatory) entry.mandatory_in_jobs += 1;
        entry.recommended_level = Math.max(entry.recommended_level, sk.required_level);
        entry.total_importance = round(entry.total_importance + sk.importance_weight, 2);
        if (entry.affected_jobs.length < 4) entry.affected_jobs.push(job.title);
      }
    }
    const roadmap = Object.values(skillImpact).sort((a, b) => {
      if (b.mandatory_in_jobs !== a.mandatory_in_jobs) return b.mandatory_in_jobs - a.mandatory_in_jobs;
      if (b.appearances_in_top_jobs !== a.appearances_in_top_jobs)
        return b.appearances_in_top_jobs - a.appearances_in_top_jobs;
      return b.total_importance - a.total_importance;
    });

    return {
      student,
      criteria: criteriaRows,
      ahp: ahpResult,
      filter_report: Object.assign({}, rejectionStats, {
        strict_passed_count: strictPassed.length,
        evaluated_pool_count: finalPool.length,
        relaxation_applied: relaxationApplied,
      }),
      topsis_matrices: topsisRes.matrices,
      ranked_jobs: rankedJobs.slice(0, 30),
      total_ranked: rankedJobs.length,
      skill_gap_roadmap: roadmap.slice(0, 10),
    };
  }

  function runWhatIfLocal(snapshot, payload) {
    const baselineRes = runPipelineLocal(snapshot, payload);
    const simStudent = JSON.parse(JSON.stringify(baselineRes.student));
    const existingMap = {};
    (simStudent.skills || []).forEach((s) => {
      existingMap[Number(s.skill_id)] = Number(s.proficiency_level);
    });
    (payload.added_skills || []).forEach((addSk) => {
      const sid = Number(addSk.skill_id);
      const lv = Number(addSk.proficiency_level || 4);
      existingMap[sid] = Math.max(existingMap[sid] || 0, lv);
    });
    simStudent.skills = Object.entries(existingMap).map(([k, v]) => ({
      skill_id: Number(k),
      proficiency_level: Number(v),
    }));
    if (payload.simulated_english_tier) {
      simStudent.english_tier = Number(payload.simulated_english_tier);
    }
    if (payload.simulated_internship_months !== undefined) {
      simStudent.internship_months = Number(payload.simulated_internship_months);
    }

    const simPayload = Object.assign({}, payload, {
      student: simStudent,
      direct_weights: payload.simulated_weights || payload.direct_weights,
      ahp_matrix: payload.simulated_ahp_matrix || payload.ahp_matrix,
    });
    const simulatedRes = runPipelineLocal(snapshot, simPayload);

    const baseMap = {};
    baselineRes.ranked_jobs.forEach((j) => {
      baseMap[j.id] = {
        rank: j.topsis.rank,
        c_star: j.topsis.c_star,
        c1_skill: j.evaluation.criteria_values.C1,
        c2_salary: j.evaluation.criteria_values.C2,
      };
    });

    const comparison = simulatedRes.ranked_jobs.slice(0, 20).map((simJob) => {
      const b = baseMap[simJob.id];
      const oldRank = b ? b.rank : null;
      const newRank = simJob.topsis.rank;
      const oldCStar = b ? b.c_star : 0.0;
      const newCStar = simJob.topsis.c_star;
      return {
        job_id: simJob.id,
        job_code: simJob.job_code,
        title: simJob.title,
        company_short: simJob.company_short,
        level: simJob.level,
        old_rank: oldRank,
        new_rank: newRank,
        rank_delta: oldRank !== null ? oldRank - newRank : 0,
        old_c_star: round(oldCStar, 4),
        new_c_star: round(newCStar, 4),
        c_star_delta: round(newCStar - oldCStar, 4),
        old_skill_score: b ? b.c1_skill : 0.0,
        new_skill_score: simJob.evaluation.criteria_values.C1,
        old_salary: b ? b.c2_salary : simJob.evaluation.criteria_values.C2,
        new_salary: simJob.evaluation.criteria_values.C2,
      };
    });

    return {
      baseline_top5: baselineRes.ranked_jobs.slice(0, 5),
      simulated_top5: simulatedRes.ranked_jobs.slice(0, 5),
      comparison,
      simulated_weights: simulatedRes.topsis_matrices.weights,
    };
  }

  window.DSSClientEngine = {
    calculateAHP,
    runPipelineLocal,
    runWhatIfLocal,
  };
})();


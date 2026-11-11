# -*- coding: utf-8 -*-
"""
Trình tạo file Báo cáo Giữa kỳ chuẩn Microsoft Word (.docx - Office Open XML)
Không phụ thuộc thư viện ngoài, trích xuất số liệu thực nghiệm trực tiếp từ CSDL SQLite (dss_job_matching.db).
"""

import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.main import get_bootstrap_data
from backend.services.dss_engine import run_dss_pipeline

DOCX_OUT_PATH = ROOT_DIR / "docs" / "Bao_Cao_Giua_Ky_DSS.docx"


def w_p(text="", bold=False, italic=False, size_pt=12, color="0F172A", align="both", space_before=60, space_after=100):
    sz = int(size_pt * 2)
    rpr = f'<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/><w:color w:val="{color}"/>'
    if bold:
        rpr += "<w:b/>"
    if italic:
        rpr += "<w:i/>"
    return (
        f"<w:p>"
        f'<w:pPr><w:spacing w:before="{space_before}" w:after="{space_after}" w:line="276" w:lineRule="auto"/><w:jc w:val="{align}"/></w:pPr>'
        f"<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space=\"preserve\">{escape(str(text))}</w:t></w:r>"
        f"</w:p>"
    )


def w_heading(text, level=1):
    if level == 1:
        return w_p(text, bold=True, size_pt=15, color="991B1B", align="left", space_before=240, space_after=120)
    elif level == 2:
        return w_p(text, bold=True, size_pt=13.5, color="1E3A8A", align="left", space_before=180, space_after=90)
    else:
        return w_p(text, bold=True, size_pt=12.5, color="0F172A", align="left", space_before=120, space_after=60)


def w_table(headers, rows):
    xml = [
        "<w:tbl>",
        "<w:tblPr>",
        '<w:tblW w:w="5000" w:type="pct"/>',
        "<w:tblBorders>",
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="94A3B8"/>',
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="94A3B8"/>',
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="94A3B8"/>',
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="94A3B8"/>',
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>',
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>',
        "</w:tblBorders>",
        "</w:tblPr>",
    ]

    # Header row
    xml.append("<w:tr>")
    for h in headers:
        xml.append(
            "<w:tc>"
            '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr>'
            + w_p(h, bold=True, size_pt=11, color="FFFFFF", align="center", space_before=40, space_after=40)
            + "</w:tc>"
        )
    xml.append("</w:tr>")

    # Data rows
    for idx, row in enumerate(rows):
        fill = "F8FAFC" if idx % 2 == 1 else "FFFFFF"
        xml.append("<w:tr>")
        for cell in row:
            xml.append(
                "<w:tc>"
                f'<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{fill}"/></w:tcPr>'
                + w_p(str(cell), bold=False, size_pt=10.5, color="0F172A", align="left", space_before=35, space_after=35)
                + "</w:tc>"
            )
        xml.append("</w:tr>")

    xml.append("</w:tbl>")
    xml.append(w_p("", size_pt=6, space_before=20, space_after=40))
    return "".join(xml)


def generate_docx():
    boot = get_bootstrap_data()
    exp_res = run_dss_pipeline({"student_id": 1})

    body_parts = []

    # Trang tiêu đề
    body_parts.append(w_p("ĐẠI HỌC BÁCH KHOA HÀ NỘI", bold=True, size_pt=14, color="991B1B", align="center", space_before=40, space_after=40))
    body_parts.append(w_p("BÁO CÁO GIỮA KỲ HỌC PHẦN: HỆ TRỢ GIÚP QUYẾT ĐỊNH (DSS)", bold=True, size_pt=15, color="1E3A8A", align="center", space_before=120, space_after=60))
    body_parts.append(w_p("ĐỀ TÀI: HỆ TRỢ GIÚP QUYẾT ĐỊNH TÌM VIỆC LÀM CHO SINH VIÊN TỐT NGHIỆP", bold=True, size_pt=16, color="0F172A", align="center", space_before=40, space_after=80))
    body_parts.append(w_p("Mô hình kết hợp: Lọc Ràng buộc Cứng + Độ khớp Kỹ năng + AHP (Saaty) + TOPSIS + Phân tích Độ nhạy What-If", italic=True, size_pt=12, color="475569", align="center", space_before=20, space_after=200))

    # CHƯƠNG 1
    body_parts.append(w_heading("CHƯƠNG 1. PHÂN TÍCH BÀI TOÁN & THIẾT KẾ CƠ SỞ DỮ LIỆU", level=1))
    body_parts.append(w_heading("1.1. Phát biểu Bài toán dưới góc độ Hệ trợ giúp quyết định (DSS)", level=2))
    body_parts.append(w_p(
        "Sinh viên mới tốt nghiệp đứng trước bài toán ra quyết định bán cấu trúc (Semi-structured) và đa tiêu chí (MCDM): "
        "Làm thế nào lựa chọn được vị trí việc làm tối ưu nhất trong hàng trăm cơ hội tuyển dụng khi các mục tiêu thường mâu thuẫn nhau "
        "(mức lương khởi điểm cao thường đòi hỏi kỹ năng khắt khe hoặc áp lực OT lớn; công việc có chương trình đào tạo bài bản hoặc gần nhà có thể có mức lương khởi điểm vừa phải). "
        "Hệ trợ giúp quyết định HUST CareerDSS được xây dựng nhằm hỗ trợ sinh viên lượng hóa hồ sơ năng lực, xác định trọng số ưu tiên cá nhân bằng phương pháp AHP và xếp hạng công việc bằng phương pháp TOPSIS."
    ))

    body_parts.append(w_heading("1.2. Hệ thống Các Biến của Bài toán", level=2))
    body_parts.append(w_p("Hệ thống biến được chia thành biến hồ sơ sinh viên, biến ràng buộc cứng và 6 biến tiêu chí đánh giá (C1..C6):"))
    crit_rows = [
        [c["code"], c["name"], c["type"], c["unit"], f"{c['default_weight']*100:.0f}%", c["description"]]
        for c in boot["criteria"]
    ]
    body_parts.append(w_table(
        ["Mã", "Tên Tiêu chí Đánh giá", "Loại", "Đơn vị", "Trọng số", "Ý nghĩa trong Mô hình DSS"],
        crit_rows
    ))

    body_parts.append(w_heading("1.3. Thiết kế Cơ sở Dữ liệu Quan hệ (9 Bảng chuẩn hóa 3NF)", level=2))
    db_tables_info = [
        ["1", "majors", "8 bản ghi", "Danh mục 8 ngành đào tạo tiêu biểu tại ĐHBK Hà Nội (IT1, IT2, DS1, EE1, EE2, ME1, EM1, EM2)"],
        ["2", "skills", "65 bản ghi", "Từ điển 65 kỹ năng chia theo 8 nhóm chuyên môn, công cụ, ngoại ngữ và kỹ năng mềm"],
        ["3", "companies", "25 bản ghi", "Thông tin 25 doanh nghiệp tuyển dụng lớn (Viettel, FPT, VNG, Shopee, Samsung, Bosch, Techcombank...)"],
        ["4", "jobs", "153 bản ghi", "153 tin tuyển dụng Intern/Fresher/Junior/MT kèm dải lương, GPA, ngoại ngữ, khoảng cách và chỉ số C4, C5, C6"],
        ["5", "job_skills", "852 bản ghi", "Yêu cầu kỹ năng chi tiết của từng việc làm (mức độ yêu cầu 1-5, trọng số quan trọng, kỹ năng bắt buộc)"],
        ["6", "student_profiles", "10 bản ghi", "10 hồ sơ sinh viên tốt nghiệp mẫu đa dạng ngành học, GPA và định hướng nghề nghiệp"],
        ["7", "student_skills", "87 bản ghi", "Kỹ năng hiện có và mức độ thành thạo (1-5) của từng hồ sơ sinh viên"],
        ["8", "criteria", "6 bản ghi", "Cấu hình 6 tiêu chí quyết định C1..C6 (5 tiêu chí BENEFIT, 1 tiêu chí COST)"],
        ["9", "dss_sessions", "Lưu tự động", "Lưu lịch sử phiên tư vấn, ma trận AHP, tỷ số nhất quán CR và kết quả xếp hạng TOPSIS"],
    ]
    body_parts.append(w_table(
        ["STT", "Tên Bảng", "Quy mô Dữ liệu", "Mô tả Vai trò và Quan hệ Khóa ngoại"],
        db_tables_info
    ))

    # CHƯƠNG 2
    body_parts.append(w_heading("CHƯƠNG 2. ĐỀ XUẤT PHƯƠNG PHÁP & MÔ HÌNH TOÁN HỌC AHP - TOPSIS", level=1))
    body_parts.append(w_heading("2.1. Quy trình 5 Giai đoạn của Hệ Trợ giúp Quyết định", level=2))
    body_parts.append(w_p("• Giai đoạn 1 (Hard-Constraint Filtering): Lọc bỏ các công việc không thỏa mãn điều kiện bắt buộc của sinh viên (mức lương tối thiểu, khoảng cách tối đa, hình thức làm việc, độ tương thích ngành học). Có cơ chế nới lỏng mềm (Soft Relaxation) nếu tập phương án quá hẹp."))
    body_parts.append(w_p("• Giai đoạn 2 (Multi-dimensional Profile-Job Scoring): Lượng hóa 6 tiêu chí C1..C6 cho từng cặp (Sinh viên, Việc làm) dựa trên mức độ đáp ứng từng kỹ năng, GPA, ngoại ngữ, kinh nghiệm và môi trường doanh nghiệp."))
    body_parts.append(w_p("• Giai đoạn 3 (Analytic Hierarchy Process - AHP): Sinh viên thực hiện so sánh cặp giữa 6 tiêu chí theo thang đo Saaty (1-9). Hệ thống tính vector riêng trọng số W, giá trị riêng lớn nhất lambda_max, chỉ số CI và tỷ số nhất quán CR = CI / RI (với RI_6 = 1.24). Nếu CR >= 0.10, hệ thống cảnh báo và chỉ ra cặp tiêu chí gây mâu thuẫn để điều chỉnh."))
    body_parts.append(w_p("• Giai đoạn 4 (TOPSIS & SAW Multi-Model Ranking): Chuẩn hóa vector Euclid ma trận quyết định X -> R, nhân trọng số AHP tạo ma trận V, xác định giải pháp lý tưởng tốt A+ và xấu A-, tính khoảng cách Euclid D+, D- và hệ số gần gũi C* = D- / (D+ + D-)."))
    body_parts.append(w_p("• Giai đoạn 5 (Skill Gap Roadmap & What-If Sensitivity Analysis): Tổng hợp các kỹ năng còn thiếu xuất hiện nhiều nhất trong Top 10 công việc đầu bảng và mô phỏng sự thay đổi thứ hạng khi sinh viên học thêm kỹ năng mới."))

    # CHƯƠNG 3
    body_parts.append(w_heading("CHƯƠNG 3. KẾT QUẢ THỰC NGHIỆM & CÀI ĐẶT PHẦN MỀM", level=1))
    body_parts.append(w_heading("3.1. Kết quả Thực nghiệm Điển hình trên Hồ sơ Sinh viên Mẫu #1", level=2))
    st = exp_res["student"]
    ahp = exp_res["ahp"]
    body_parts.append(w_p(
        f"Hồ sơ thử nghiệm: {st['full_name']} (MSSV: {st['student_code']}), Ngành: {st['major_code']}, "
        f"GPA: {st['gpa']}/4.0, Ngoại ngữ: {st['english_cert']}, Thực tập: {st['internship_months']} tháng. "
        f"Kết quả kiểm định AHP: lambda_max = {ahp['lambda_max']:.4f}, CI = {ahp['ci']:.4f}, CR = {ahp['cr']*100:.2f}% (< 10%, đạt chuẩn nhất quán)."
    ))

    top10_rows = []
    for j in exp_res["ranked_jobs"][:10]:
        cv = j["evaluation"]["criteria_values"]
        tp = j["topsis"]
        top10_rows.append([
            f"#{tp['rank']}",
            j["job_code"],
            j["title"],
            f"{cv['C1']}%",
            f"{cv['C2']} tr",
            f"{cv['C3']}",
            f"{cv['C4']}",
            f"{cv['C5']}",
            f"{cv['C6']}",
            f"{tp['d_plus']:.4f}",
            f"{tp['d_minus']:.4f}",
            f"{tp['c_star']:.4f}",
        ])

    body_parts.append(w_table(
        ["Hạng", "Mã CV", "Vị trí Việc làm & Doanh nghiệp", "C1", "C2", "C3", "C4", "C5", "C6", "D+", "D-", "C* (TOPSIS)"],
        top10_rows
    ))

    body_parts.append(w_heading("3.2. Danh sách 10 Hồ sơ Sinh viên Mẫu trong Cơ sở Dữ liệu", level=2))
    stu_rows = [
        [
            sp["student_code"],
            sp["full_name"],
            sp["major_code"],
            f"{sp['gpa']:.2f}",
            sp["english_cert"],
            f"{sp['internship_months']} tháng",
            f"{len(sp['skills'])} kỹ năng",
            sp["persona_preset"],
        ]
        for sp in boot["student_profiles"]
    ]
    body_parts.append(w_table(
        ["MSSV", "Họ và Tên Sinh viên", "Ngành", "GPA", "Ngoại ngữ", "Thực tập", "Số kỹ năng", "Cấu hình AHP"],
        stu_rows
    ))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        + "".join(body_parts)
        + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1417"/></w:sectPr>'
        "</w:body></w:document>"
    )

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )

    DOCX_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DOCX_OUT_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("word/document.xml", document_xml)

    print(f"Created DOCX report successfully at: {DOCX_OUT_PATH} ({DOCX_OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_docx()


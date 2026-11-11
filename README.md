# HUST CareerDSS — Hệ Trợ Giúp Quyết Định Tìm Việc Làm Cho Sinh Viên Tốt Nghiệp

Đồ án môn học **Hệ trợ giúp quyết định (Decision Support Systems - DSS)** tại Đại học Bách Khoa Hà Nội (HUST).

---

## 1. Cấu trúc Dự án

```text
Hệ trợ giúp quyết định/
├── backend/
│   ├── database/
│   │   ├── schema.sql                     # Lược đồ CSDL quan hệ (9 bảng chuẩn 3NF)
│   │   ├── seed_data.py                   # Script sinh dữ liệu mẫu (153 việc làm, 65 kỹ năng, 25 công ty, 10 hồ sơ SV)
│   │   ├── dss_job_matching.db            # Tệp CSDL SQLite đã nạp đầy đủ dữ liệu
│   │   ├── export_frontend_snapshot.py    # Script xuất Snapshot dữ liệu từ SQLite sang JSON/JS
│   │   └── full_dataset_dump.json         # Bản sao toàn bộ dữ liệu định dạng JSON
│   ├── services/
│   │   └── dss_engine.py                  # Bộ xử lý mô hình toán học (Hard Filter, Skill Matching, AHP, TOPSIS, SAW, What-If)
│   ├── tests/
│   │   └── test_dss_engine.py             # Kiểm thử tự động đơn vị và tích hợp cho mô hình DSS
│   ├── main.py                            # Máy chủ REST API & phục vụ giao diện Web tại cổng 8000
│   └── requirements.txt                   # Danh sách thư viện Python
├── frontend/
│   ├── index.html                         # Giao diện chính Hệ trợ giúp quyết định (5 màn hình chuyên sâu)
│   ├── package.json
│   └── src/
│       ├── app.js                         # Logic điều khiển giao diện, biểu đồ SVG Radar & tương tác AHP/TOPSIS/What-If
│       ├── dss_client_engine.js           # Bộ giải toán học đồng bộ phía Client & kết nối API SQLite
│       ├── styles.css                     # Giao diện Dashboard hiện đại
│       └── data/
│           └── db_snapshot.js             # Snapshot CSDL tự động sinh từ SQLite
├── docs/
│   ├── Bao_Cao_Giua_Ky_DSS.md             # Báo cáo giữa kỳ & phân tích bài toán chi tiết (kèm sơ đồ ERD, công thức LaTeX)
│   ├── Bao_Cao_Giua_Ky_DSS.docx           # Báo cáo giữa kỳ định dạng Microsoft Word (.docx)
│   └── generate_docx_report.py            # Script tự động sinh báo cáo Word từ số liệu thực nghiệm CSDL
└── run_dss_app.bat                        # Tệp khởi chạy nhanh (1-click) mở Server & Trình duyệt
```

---

## 2. Hướng dẫn Chạy Nhanh

### Cách 1: Chạy đầy đủ Máy chủ Python + SQLite REST API + Giao diện Web
Nháy đúp vào tệp **`run_dss_app.bat`** hoặc mở Terminal chạy:
```powershell
python backend/main.py
```
Sau đó truy cập địa chỉ: **`http://127.0.0.1:8000`**

### Cách 2: Mở trực tiếp Giao diện Trợ giúp Quyết định (Không cần bật Server)
Mở trực tiếp tệp **`frontend/index.html`** bằng trình duyệt bất kỳ (Chrome / Edge / Firefox). Hệ thống tự động nạp bản Snapshot của toàn bộ 153 việc làm và 10 hồ sơ sinh viên từ `dss_job_matching.db`.

### Chạy Kiểm thử Tự động Mô hình Toán học (AHP - TOPSIS - What-If)
```powershell
python backend/tests/test_dss_engine.py
```


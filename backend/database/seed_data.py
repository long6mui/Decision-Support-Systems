# -*- coding: utf-8 -*-
"""
Script khởi tạo Cơ sở dữ liệu (SQLite) & Dữ liệu mẫu phong phú cho đề tài:
HỆ TRỢ GIÚP QUYẾT ĐỊNH: TRỢ GIÚP SINH VIÊN TỐT NGHIỆP TÌM VIỆC LÀM
Đại học Bách Khoa Hà Nội (HUST)
"""

import json
import os
import random
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
DB_PATH = BASE_DIR / "dss_job_matching.db"
SEED_EXPORT_JSON = BASE_DIR / "seed_preview.json"

# 1. Danh mục 8 ngành đào tạo tiêu biểu tại ĐHBK Hà Nội (HUST)
MAJORS = [
    ("IT1", "Khoa học Máy tính (Computer Science)", "Trường CNTT & Truyền thông (SoICT)", "Chuyên sâu về AI, Khoa học dữ liệu, Thuật toán, Hệ thống phần mềm thông minh."),
    ("IT2", "Kỹ thuật Máy tính & Phần mềm (Software/Computer Eng.)", "Trường CNTT & Truyền thông (SoICT)", "Chuyên sâu về phát triển phần mềm, Web/Mobile, Cloud, DevOps, Hệ thống nhúng."),
    ("DS1", "Khoa học Dữ liệu & Trí tuệ Nhân tạo (Data Science & AI)", "Trường CNTT & Truyền thông (SoICT)", "Chuyên sâu về Machine Learning, Deep Learning, NLP, Computer Vision, Big Data Engineering."),
    ("EE1", "Kỹ thuật Điện - Điện tử Viễn thông", "Trường Điện - Điện tử (SEEE)", "Thiết kế vi mạch, phần cứng, IoT, hệ thống viễn thông 5G, năng lượng thông minh."),
    ("EE2", "Kỹ thuật Điều khiển & Tự động hóa", "Trường Điện - Điện tử (SEEE)", "PLC, SCADA, Robotics, Điều khiển quá trình công nghiệp, Nhà máy thông minh."),
    ("ME1", "Kỹ thuật Cơ điện tử (Mechatronics)", "Trường Cơ khí (SME)", "Thiết kế cơ khí CAD/CAM/CAE, Robot công nghiệp, Hệ thống cơ điện tử tích hợp."),
    ("EM1", "Hệ thống Thông tin Quản lý (MIS & Business Analytics)", "Trường Kinh tế (SEM)", "Phân tích nghiệp vụ (BA), ERP, Quản trị dự án CNTT, Phân tích dữ liệu kinh doanh."),
    ("EM2", "Quản trị Kinh doanh Công nghệ & Logistics", "Trường Kinh tế (SEM)", "Vận hành chuỗi cung ứng, Quản lý sản phẩm (Product), Digital Marketing, FinTech Operations."),
]

# 2. Danh mục 65 kỹ năng phân theo 8 nhóm
SKILLS = [
    # Programming (1..12)
    ("Python", "Programming", "Ngôn ngữ lập trình đa dụng cho AI, Data, Backend"),
    ("Java", "Programming", "Ngôn ngữ lập trình hướng đối tượng cho hệ thống Enterprise/Ngân hàng"),
    ("JavaScript / TypeScript", "Programming", "Ngôn ngữ phát triển Web Frontend & Fullstack"),
    ("C / C++", "Programming", "Ngôn ngữ hiệu năng cao cho Nhúng, Vi mạch, Thuật toán"),
    ("C# / .NET", "Programming", "Nền tảng phát triển phần mềm doanh nghiệp của Microsoft"),
    ("Golang", "Programming", "Ngôn ngữ lập trình hệ thống phân tán, Microservices hiệu năng cao"),
    ("SQL & Cơ sở dữ liệu", "Programming", "Truy vấn và thiết kế CSDL quan hệ PostgreSQL/MySQL/Oracle"),
    ("Cấu trúc dữ liệu & Giải thuật", "Programming", "Nền tảng tư duy thuật toán và tối ưu hóa"),
    ("Lập trình Hướng đối tượng (OOP)", "Programming", "Nguyên lý thiết kế phần mềm SOLID, Design Patterns"),
    ("Rust", "Programming", "Ngôn ngữ hệ thống an toàn bộ nhớ"),
    ("MATLAB / Simulink", "Programming", "Mô phỏng tính toán kỹ thuật, điều khiển, xử lý tín hiệu"),
    ("R / Thống kê ứng dụng", "Programming", "Phân tích thống kê và mô hình hóa dữ liệu"),

    # Web_Mobile (13..22)
    ("React.js / Next.js", "Web_Mobile", "Thư viện và framework phát triển giao diện Web hiện đại"),
    ("Node.js / Express / NestJS", "Web_Mobile", "Xây dựng RESTful API & Realtime Backend"),
    ("Spring Boot", "Web_Mobile", "Framework Java phổ biến nhất cho Microservices & Banking"),
    ("FastAPI / Django", "Web_Mobile", "Framework phát triển Web API bằng Python"),
    ("Flutter / React Native", "Web_Mobile", "Phát triển ứng dụng di động đa nền tảng"),
    ("HTML5 / CSS3 / Tailwind", "Web_Mobile", "Thiết kế giao diện Web đáp ứng (Responsive UI)"),
    ("RESTful API / GraphQL", "Web_Mobile", "Thiết kế và tích hợp dịch vụ Web"),
    ("Android (Kotlin) / iOS (Swift)", "Web_Mobile", "Phát triển ứng dụng di động Native"),
    ("Microservices Architecture", "Web_Mobile", "Kiến trúc dịch vụ phân tán quy mô lớn"),
    ("Automated Testing / Selenium", "Web_Mobile", "Kiểm thử tự động phần mềm QA/Automation QC"),

    # Data_AI (23..32)
    ("Machine Learning (Scikit-learn/XGBoost)", "Data_AI", "Huấn luyện mô hình học máy có giám sát và không giám sát"),
    ("Deep Learning (PyTorch / TensorFlow)", "Data_AI", "Mạng nơ-ron sâu cho thị giác máy tính và xử lý ngôn ngữ"),
    ("Xử lý Ngôn ngữ Tự nhiên (NLP / LLM / RAG)", "Data_AI", "Ứng dụng mô hình ngôn ngữ lớn, Chatbot, trích xuất thông tin"),
    ("Thị giác Máy tính (Computer Vision / OpenCV)", "Data_AI", "Nhận diện ảnh, video, OCR, kiểm tra lỗi sản phẩm công nghiệp"),
    ("Phân tích Dữ liệu (Pandas / NumPy)", "Data_AI", "Làm sạch, biến đổi và khai phá dữ liệu (EDA)"),
    ("Power BI / Tableau", "Data_AI", "Trực quan hóa dữ liệu và xây dựng Dashboard báo cáo"),
    ("Apache Spark / Kafka / Airflow", "Data_AI", "Xây dựng đường ống dữ liệu lớn (Big Data Pipeline / ETL)"),
    ("Data Warehouse (Snowflake / BigQuery)", "Data_AI", "Kho dữ liệu đám mây và mô hình hóa chiều (Star Schema)"),
    ("MLOps (MLflow / Docker for AI)", "Data_AI", "Triển khai và giám sát mô hình AI trên môi trường thực tế"),
    ("Xác suất Thống kê & Tối ưu hóa", "Data_AI", "Toán ứng dụng cho Khoa học dữ liệu và Hệ trợ giúp quyết định"),

    # System_DevOps (33..40)
    ("Git / GitHub / GitLab CI", "System_DevOps", "Quản lý phiên bản mã nguồn và cộng tác nhóm"),
    ("Docker & Containerization", "System_DevOps", "Đóng gói và triển khai ứng dụng bằng Container"),
    ("Kubernetes (K8s)", "System_DevOps", "Điều phối container tự động trên Cloud"),
    ("AWS / Google Cloud / Azure", "System_DevOps", "Dịch vụ điện toán đám mây công cộng"),
    ("Linux / Shell Scripting", "System_DevOps", "Quản trị hệ điều hành máy chủ Linux và tự động hóa Bash"),
    ("CI/CD Pipelines (Jenkins / GitHub Actions)", "System_DevOps", "Tự động hóa tích hợp và triển khai liên tục"),
    ("An toàn thông tin (Cybersecurity / Pentest)", "System_DevOps", "Bảo mật ứng dụng Web, mạng và kiểm thử xâm nhập"),
    ("Redis / Elasticsearch / Message Queue", "System_DevOps", "Tối ưu bộ nhớ đệm và tìm kiếm toàn văn"),

    # Embedded_Hardware (41..48)
    ("Vi điều khiển (STM32 / ARM / ESP32)", "Embedded_Hardware", "Lập trình固件 (Firmware) cho thiết bị nhúng và IoT"),
    ("RTOS / Embedded Linux", "Embedded_Hardware", "Hệ điều hành thời gian thực cho hệ thống nhúng"),
    ("Thiết kế Vi mạch (Verilog / VHDL / FPGA)", "Embedded_Hardware", "Thiết kế IC số, ASIC, FPGA Verification"),
    ("Thiết kế Mạch PCB (Altium / OrCAD)", "Embedded_Hardware", "Thiết kế sơ đồ nguyên lý và mạch in phần cứng"),
    ("PLC / SCADA / HMI (Siemens / Mitsubishi)", "Embedded_Hardware", "Lập trình điều khiển tự động hóa dây chuyền công nghiệp"),
    ("CAD / CAM / SolidWorks / AutoCAD", "Embedded_Hardware", "Thiết kế cơ khí 3D và mô phỏng kết cấu"),
    ("ROS / Robot Điều khiển Chuyển động", "Embedded_Hardware", "Hệ điều hành Robot và điều khiển động cơ Servo/Step"),
    ("Giao thức Công nghiệp (CAN / Modbus / MQTT)", "Embedded_Hardware", "Truyền thông thiết bị IoT, ô tô và nhà máy"),

    # Business_Domain (49..56)
    ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", "Business_Domain", "Thu thập yêu cầu, viết tài liệu SRS/BRD, vẽ quy trình"),
    ("Quản lý Sản phẩm (Product Management / Agile Scrum)", "Business_Domain", "Xây dựng Product Backlog, User Story, Roadmap"),
    ("Hệ thống ERP (SAP / Odoo)", "Business_Domain", "Tư vấn và triển khai phần mềm hoạch định nguồn lực doanh nghiệp"),
    ("Phân tích Tài chính & Rủi ro (FinTech / Credit Scoring)", "Business_Domain", "Đánh giá rủi ro tín dụng, ngân hàng số, thanh toán"),
    ("Quản trị Chuỗi cung ứng & Logistics (Supply Chain)", "Business_Domain", "Tối ưu tồn kho, vận tải, dự báo nhu cầu"),
    ("Digital Marketing & Growth Analytics", "Business_Domain", "Phân tích hành vi người dùng, phễu chuyển đổi, A/B Testing"),
    ("UI/UX Design & Figma Prototyping", "Business_Domain", "Thiết kế trải nghiệm người dùng và nguyên mẫu giao diện"),
    ("Excel Nâng cao & VBA", "Business_Domain", "Mô hình hóa bảng tính và tự động hóa báo cáo văn phòng"),

    # SoftSkill (57..61)
    ("Giải quyết vấn đề & Tư duy phản biện", "SoftSkill", "Phân tích nguyên nhân gốc rễ và ra quyết định logic"),
    ("Làm việc nhóm & Giao tiếp Kỹ thuật", "SoftSkill", "Phối hợp đa phòng ban và trình bày giải pháp rõ ràng"),
    ("Thuyết trình & Viết báo cáo chuyên nghiệp", "SoftSkill", "Trình bày ý tưởng trước khách hàng và ban lãnh đạo"),
    ("Quản lý thời gian & Chịu áp lực công việc", "SoftSkill", "Hoàn thành deadline trong môi trường tốc độ cao"),
    ("Khả năng tự học công nghệ mới", "SoftSkill", "Chủ động nghiên cứu tài liệu tiếng Anh và thích nghi nhanh"),

    # Language (62..65)
    ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", "Language", "Tương đương TOEIC 600+ / IELTS 5.5+"),
    ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", "Language", "Làm việc trực tiếp với khách hàng Âu - Mỹ - Sing"),
    ("Tiếng Nhật (JLPT N3 / N2)", "Language", "Làm việc với doanh nghiệp Nhật Bản / BrSE"),
    ("Tiếng Hàn / Tiếng Trung Giao tiếp", "Language", "Làm việc tại các tập đoàn FDI Hàn Quốc / Đài Loan / Trung Quốc"),
]

# 3. Danh mục 25 Doanh nghiệp Tuyển dụng tại Việt Nam
COMPANIES = [
    ("Tập đoàn Công nghiệp - Viễn thông Quân đội (Viettel)", "Viettel", "Telecom, AI, CyberSecurity & Aerospace", "Enterprise", 4.5, "Cầu Giấy", "Hà Nội", "https://viettel.com.vn", "Tập đoàn công nghệ - viễn thông hàng đầu Việt Nam với chế độ đãi ngộ và thưởng quý/năm rất tốt cho kỹ sư Bách Khoa."),
    ("FPT Software", "FPT Software", "Global IT Services & Digital Transformation", "Enterprise", 4.1, "Thạch Thất (Hòa Lạc) / Cầu Giấy", "Hà Nội", "https://fptsoftware.com", "Công ty phần mềm lớn nhất Việt Nam, có chương trình Fresher Academy đào tạo bài bản và cơ hội onsite Nhật, Mỹ, Châu Âu."),
    ("VNG Corporation", "VNG", "Internet, Cloud, Gaming, Zalo & AI", "Large", 4.4, "Đống Đa", "Hà Nội", "https://vng.com.vn", "Kỳ lân công nghệ Việt Nam, môi trường kỹ thuật chuyên sâu, đãi ngộ cao cho Fresher/Junior xuất sắc."),
    ("Shopee / Sea Group Vietnam", "Shopee VN", "E-Commerce & FinTech (ShopeePay)", "MNC", 4.3, "Ba Đình", "Hà Nội", "https://careers.shopee.vn", "Tập đoàn thương mại điện tử hàng đầu Đông Nam Á, nổi tiếng với chương trình Global Leaders Program và kỹ sư dữ liệu."),
    ("VinBigdata / Vingroup Tech", "VinBigdata", "Generative AI, Smart City & Automotive AI", "Large", 4.2, "Long Biên", "Hà Nội", "https://vinbigdata.com", "Nghiên cứu và phát triển các giải pháp AI, LLM tiếng Việt, trợ lý ảo ViVi với mức lương cạnh tranh."),
    ("Samsung R&D Institute Vietnam (SRV)", "Samsung R&D", "Mobile R&D, Embedded, AI & Network", "MNC", 4.4, "Bắc Từ Liêm (Tây Hồ Tây)", "Hà Nội", "https://samsung.com/vn", "Trung tâm R&D lớn nhất Đông Nam Á của Samsung, tuyển dụng quy mô lớn sinh viên tốt nghiệp HUST qua kỳ thi GSAT/SW Test."),
    ("Bosch Global Software Technologies Vietnam", "Bosch VN", "Automotive Embedded, IoT & Enterprise IT", "MNC", 4.5, "Ba Đình", "Hà Nội", "https://bosch.com.vn", "Tập đoàn công nghệ Đức với môi trường làm việc chuẩn Âu, cân bằng cuộc sống (Work-Life Balance) và đào tạo chuyên sâu."),
    ("LG Electronics Development Vietnam (LGDV)", "LG R&D", "Automotive Infotainment, WebOS & Embedded", "MNC", 4.3, "Nam Từ Liêm (Keangnam)", "Hà Nội", "https://lg.com/vn", "Trung tâm R&D phần mềm ô tô và thiết bị thông minh của LG tại Hà Nội, đãi ngộ tốt cho kỹ sư C/C++ và Điện tử."),
    ("Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)", "Techcombank", "Digital Banking, Data Analytics & Cloud", "Enterprise", 4.4, "Hoàn Kiếm", "Hà Nội", "https://techcombank.com", "Ngân hàng đi đầu về chuyển đổi số, dữ liệu lớn và AI tài chính với thu nhập thuộc nhóm cao nhất khối ngân hàng."),
    ("Công ty Cổ phần MISA", "MISA", "SaaS, ERP, FinTech & AI Accounting", "Large", 4.1, "Cầu Giấy", "Hà Nội", "https://misa.vn", "Doanh nghiệp phần mềm sản phẩm hàng đầu Việt Nam, lộ trình đào tạo thực chiến tốt cho sinh viên mới ra trường."),
    ("CMC Global / CMC Technology", "CMC", "Cloud, Software Outsourcing & Security", "Large", 4.0, "Cầu Giấy", "Hà Nội", "https://cmcglobal.com.vn", "Tập đoàn công nghệ lớn tại Hà Nội, nhiều vị trí Fresher/Junior Java, .NET, React, QA, BA."),
    ("NashTech Vietnam", "NashTech", "Software Engineering, Data & Cloud", "MNC", 4.3, "Cầu Giấy", "Hà Nội", "https://nashtechglobal.com", "Công ty công nghệ thuộc tập đoàn Harvey Nash (Anh Quốc), văn hóa làm việc tôn trọng cá nhân, đào tạo Rookie2Engineer uy tín."),
    ("Sun* Inc. (Sun Asterisk Vietnam)", "Sun*", "Digital Creative Studio & Japan IT", "Large", 4.2, "Nam Từ Liêm", "Hà Nội", "https://sun-asterisk.vn", "Môi trường trẻ trung, mạnh về đào tạo sinh viên Bách Khoa chương trình Việt-Nhật (HEDSPI) và phát triển sản phẩm Web/AI."),
    ("One Mount Group", "One Mount", "Tech Ecosystem (VinShop, OneHousing, FinTech)", "Large", 4.3, "Hai Bà Trưng (Times City)", "Hà Nội", "https://onemount.com", "Hệ sinh thái công nghệ lớn, vị trí gần ĐHBK Hà Nội, chế độ lương thưởng và thiết bị làm việc hiện đại."),
    ("Ngân hàng TMCP Quân Đội (MB Bank Digital)", "MB Bank", "Banking IT, App MBBank, Core Banking & BA", "Enterprise", 4.2, "Cầu Giấy", "Hà Nội", "https://mbbank.com.vn", "Sở hữu siêu ứng dụng ngân hàng số hàng chục triệu người dùng, nhu cầu tuyển lớn kỹ sư Backend, Mobile, Data, BA."),
    ("FPT Smart Cloud (FPT.AI)", "FPT Smart Cloud", "Cloud Computing, Conversational AI & GPU Cloud", "Large", 4.3, "Cầu Giấy", "Hà Nội", "https://fptsmartcloud.com", "Đơn vị mũi nhọn về AI và Cloud của FPT, phù hợp với sinh viên định hướng AI Engineer, Cloud/DevOps."),
    ("Dolphin Technology Vietnam Center", "Dolphin Tech", "Semiconductor, IC Design & Layout", "MNC", 4.3, "Cầu Giấy", "Hà Nội", "https://dolphin-vc.com", "Công ty thiết kế vi mạch bán dẫn Hoa Kỳ tại Hà Nội, điểm đến hàng đầu cho kỹ sư Điện tử - Viễn thông HUST."),
    ("FPT Semiconductor & Synopsys Partner Lab", "FPT Semi", "VLSI, FPGA, Physical Design & Verification", "Large", 4.2, "Cầu Giấy", "Hà Nội", "https://fpt.com", "Phát triển chip bán dẫn thương hiệu Việt, ưu tiên kỹ sư Điện - Điện tử và Kỹ thuật máy tính."),
    ("ABB Automation & Robotics Vietnam", "ABB Vietnam", "Industrial Automation, Robotics & Smart Grid", "MNC", 4.5, "Hoàng Mai / Bắc Ninh", "Hà Nội", "https://global.abb", "Tập đoàn Thụy Điển - Thụy Sĩ dẫn đầu về điện khí hóa và tự động hóa công nghiệp, PLC, SCADA, Robot."),
    ("Siemens Vietnam", "Siemens", "Factory Automation, Digital Industries & Smart Infra", "MNC", 4.6, "Đống Đa", "Hà Nội", "https://siemens.com.vn", "Tập đoàn công nghệ công nghiệp Đức, chế độ phúc lợi hàng đầu cho kỹ sư Tự động hóa và Điện."),
    ("Canon Vietnam (Thăng Long / Quế Võ)", "Canon VN", "Mechatronics, Manufacturing Engineering & QA", "MNC", 4.0, "Đông Anh (KCN Bắc Thăng Long)", "Hà Nội", "https://canon.com.vn", "Doanh nghiệp chế tạo lớn của Nhật Bản, có xe đưa đón từ nội thành Hà Nội, tuyển nhiều kỹ sư Cơ điện tử, Tự động hóa."),
    ("Viettel High Tech (VHT)", "Viettel High Tech", "5G Hardware, Radar, Aerospace & Embedded AI", "Enterprise", 4.5, "Cầu Giấy / Hòa Lạc", "Hà Nội", "https://viettelhightech.vn", "Tổng công ty Công nghệ cao Viettel, nghiên cứu thiết bị 5G, chip, tự động hóa và hệ thống nhúng phức tạp."),
    ("MoMo (M_Service)", "MoMo", "Super App, FinTech, AI Recommender & Big Data", "Large", 4.3, "Đống Đa", "Hà Nội", "https://momo.vn", "Siêu ứng dụng tài chính, bài toán dữ liệu lớn và gợi ý cá nhân hóa thời gian thực."),
    ("Base.vn (FPT Base)", "Base.vn", "B2B SaaS Platform & Product Management", "SME", 4.2, "Cầu Giấy", "Hà Nội", "https://base.vn", "Nền tảng quản trị doanh nghiệp SaaS phổ biến tại Việt Nam, phù hợp với Web Developer, Product Manager, BA."),
    ("KPMG Digital & Tech Consulting Vietnam", "KPMG Vietnam", "ERP Consulting, Data Analytics, IT Audit & BA", "MNC", 4.3, "Nam Từ Liêm", "Hà Nội", "https://kpmg.com/vn", "Tập đoàn tư vấn Big4, lộ trình thăng tiến rõ ràng cho sinh viên ngành Hệ thống thông tin quản lý (MIS) và Kinh tế công nghệ."),
]

# 4. Danh mục 6 Tiêu chí Đánh giá chuẩn trong Mô hình DSS (AHP - TOPSIS)
CRITERIA = [
    (
        "C1",
        "Độ khớp Kỹ năng Chuyên môn & Công nghệ",
        "Độ khớp Kỹ năng",
        "BENEFIT",
        "Điểm (0-100)",
        0.28,
        "Mức độ đáp ứng bộ kỹ năng bắt buộc và kỹ năng ưu tiên của công việc dựa trên mức độ thành thạo (1-5) của sinh viên.",
        "Tính theo tổng trọng số mức đáp ứng kỹ năng có xét hệ số phạt nếu thiếu kỹ năng bắt buộc."
    ),
    (
        "C2",
        "Mức Thu nhập Kỳ vọng & Đãi ngộ Tài chính",
        "Mức Lương",
        "BENEFIT",
        "Triệu VNĐ/tháng",
        0.22,
        "Mức lương khởi điểm ước tính cho sinh viên dựa trên dải lương công việc và năng lực thực tế của ứng viên.",
        "Nội suy trong khoảng [salary_min, salary_max] theo năng lực ứng viên."
    ),
    (
        "C3",
        "Độ phù hợp Học vấn, Chuyên ngành & Ngoại ngữ",
        "Độ hợp Hồ sơ",
        "BENEFIT",
        "Điểm (0-10)",
        0.16,
        "Mức độ tương thích giữa ngành đào tạo, điểm GPA, trình độ ngoại ngữ và số tháng kinh nghiệm thực tập của sinh viên với yêu cầu tuyển dụng.",
        "Tổng hợp từ độ khớp ngành học (40%), GPA (25%), Ngoại ngữ (20%) và Kinh nghiệm (15%)."
    ),
    (
        "C4",
        "Cơ hội Đào tạo, Mentorship & Thăng tiến",
        "Đào tạo & Phát triển",
        "BENEFIT",
        "Điểm (1-10)",
        0.15,
        "Chất lượng chương trình đào tạo Fresher/Junior, người hướng dẫn (Mentor), lộ trình xét tăng lương và phát triển sự nghiệp dài hạn.",
        "Trích xuất từ chỉ số đào tạo của vị trí và uy tín phát triển nhân tài của doanh nghiệp."
    ),
    (
        "C5",
        "Phúc lợi, Văn hóa & Uy tín Doanh nghiệp",
        "Phúc lợi & Văn hóa",
        "BENEFIT",
        "Điểm (1-10)",
        0.10,
        "Chế độ bảo hiểm, thưởng dự án, môi trường làm việc, đánh giá của nhân viên và thương hiệu nhà tuyển dụng trên thị trường.",
        "Kết hợp điểm phúc lợi vị trí (70%) và điểm đánh giá doanh nghiệp quy đổi (30%)."
    ),
    (
        "C6",
        "Chi phí Khoảng cách Di chuyển & Áp lực OT",
        "Khoảng cách & Áp lực",
        "COST",
        "Điểm chi phí (1-10)",
        0.09,
        "Tiêu chí CHI PHÍ (càng thấp càng tốt): phản ánh thời gian/khoảng cách đi lại hàng ngày kết hợp với mức độ áp lực làm thêm giờ (Overtime).",
        "Kết hợp khoảng cách địa lý có xét hình thức Remote/Hybrid (50%) và chỉ số áp lực OT (50%)."
    ),
]


def build_jobs_catalog():
    """
    Sinh danh sách 108 việc làm phong phú, thực tế cho cả 8 ngành tại HUST.
    Mỗi công việc có bộ kỹ năng bắt buộc + ưu tiên riêng biệt, mức lương, GPA, ngoại ngữ, khoảng cách và các chỉ số C4, C5, C6.
    """
    # Định nghĩa các mẫu việc làm thực tế theo từng nhóm ngành
    job_templates = [
        # --- Nhóm IT1 / IT2: Backend, Frontend, Fullstack, Mobile, Cloud/DevOps, Security, QA ---
        {
            "title": "Fresher Backend Engineer (Java Spring Boot)",
            "major_code": "IT2",
            "level": "Fresher",
            "companies": ["Viettel", "Techcombank", "MB Bank", "FPT Software", "CMC", "MISA"],
            "salary_range": (11.0, 18.0),
            "min_gpa": 2.7,
            "min_eng": 3,
            "min_exp": 3,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (7.8, 9.2),
            "welfare": (7.5, 9.0),
            "pressure": (5.5, 7.8),
            "skills": [
                ("Java", 3, 3.0, 1),
                ("Spring Boot", 3, 2.8, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.5, 1),
                ("Lập trình Hướng đối tượng (OOP)", 4, 2.0, 1),
                ("RESTful API / GraphQL", 3, 2.0, 0),
                ("Git / GitHub / GitLab CI", 3, 1.5, 0),
                ("Docker & Containerization", 2, 1.5, 0),
            ],
            "desc": "Tham gia phát triển các phân hệ Core Backend, Microservices phục vụ hàng triệu người dùng với kiến trúc Java Spring Boot."
        },
        {
            "title": "Junior Software Engineer (Golang / Distributed Systems)",
            "major_code": "IT1",
            "level": "Junior",
            "companies": ["VNG", "Shopee VN", "One Mount", "MoMo"],
            "salary_range": (16.0, 26.0),
            "min_gpa": 3.0,
            "min_eng": 4,
            "min_exp": 6,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.5, 9.5),
            "welfare": (8.5, 9.5),
            "pressure": (6.5, 8.2),
            "skills": [
                ("Golang", 3, 3.0, 1),
                ("Cấu trúc dữ liệu & Giải thuật", 4, 3.0, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.5, 1),
                ("Redis / Elasticsearch / Message Queue", 3, 2.2, 0),
                ("Docker & Containerization", 3, 2.0, 0),
                ("Microservices Architecture", 3, 2.0, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4, 1.8, 0),
            ],
            "desc": "Xây dựng các hệ thống chịu tải cao (High Concurrency), tối ưu độ trễ API cho nền tảng thanh toán và thương mại điện tử."
        },
        {
            "title": "Fresher Frontend / Fullstack Developer (React & TypeScript)",
            "major_code": "IT2",
            "level": "Fresher",
            "companies": ["Sun*", "Base.vn", "NashTech", "FPT Software", "MISA", "One Mount"],
            "salary_range": (10.0, 17.0),
            "min_gpa": 2.5,
            "min_eng": 3,
            "min_exp": 3,
            "work_modes": ["Hybrid", "Onsite", "Remote"],
            "training": (7.5, 9.0),
            "welfare": (7.5, 8.8),
            "pressure": (4.5, 6.8),
            "skills": [
                ("JavaScript / TypeScript", 3, 3.0, 1),
                ("React.js / Next.js", 3, 3.0, 1),
                ("HTML5 / CSS3 / Tailwind", 4, 2.2, 1),
                ("Node.js / Express / NestJS", 2, 2.0, 0),
                ("RESTful API / GraphQL", 3, 1.8, 0),
                ("Git / GitHub / GitLab CI", 3, 1.5, 0),
            ],
            "desc": "Phát triển giao diện Web App hiện đại với React/Next.js, tối ưu hóa trải nghiệm người dùng và tích hợp API thời gian thực."
        },
        {
            "title": "Python Backend & Cloud Developer (FastAPI / Django)",
            "major_code": "IT2",
            "level": "Fresher",
            "companies": ["FPT Smart Cloud", "VinBigdata", "NashTech", "Sun*"],
            "salary_range": (11.0, 18.5),
            "min_gpa": 2.6,
            "min_eng": 3,
            "min_exp": 3,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.0, 9.0),
            "welfare": (7.8, 8.8),
            "pressure": (5.0, 7.0),
            "skills": [
                ("Python", 4, 3.0, 1),
                ("FastAPI / Django", 3, 2.8, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.5, 1),
                ("Docker & Containerization", 3, 2.0, 0),
                ("AWS / Google Cloud / Azure", 2, 1.8, 0),
                ("Linux / Shell Scripting", 3, 1.5, 0),
            ],
            "desc": "Xây dựng các dịch vụ Backend API hiệu năng cao trên nền tảng Python FastAPI/Django và triển khai trên hạ tầng Cloud."
        },
        {
            "title": "Fresher Mobile App Developer (Flutter / Kotlin / Swift)",
            "major_code": "IT2",
            "level": "Fresher",
            "companies": ["Samsung R&D", "MB Bank", "MoMo", "VNG", "FPT Software"],
            "salary_range": (11.0, 18.0),
            "min_gpa": 2.6,
            "min_eng": 3,
            "min_exp": 2,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (8.0, 9.2),
            "welfare": (7.8, 9.0),
            "pressure": (5.2, 7.2),
            "skills": [
                ("Flutter / React Native", 3, 2.8, 1),
                ("Android (Kotlin) / iOS (Swift)", 3, 2.6, 0),
                ("Lập trình Hướng đối tượng (OOP)", 3, 2.5, 1),
                ("RESTful API / GraphQL", 3, 2.0, 1),
                ("Git / GitHub / GitLab CI", 3, 1.5, 0),
            ],
            "desc": "Phát triển ứng dụng di động thông minh với giao diện mượt mà, bảo mật cao trên Android/iOS."
        },
        {
            "title": "Fresher DevOps / Cloud Infrastructure Engineer",
            "major_code": "IT1",
            "level": "Fresher",
            "companies": ["Viettel", "FPT Smart Cloud", "VNG", "CMC", "Techcombank"],
            "salary_range": (12.0, 20.0),
            "min_gpa": 2.7,
            "min_eng": 4,
            "min_exp": 3,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.0, 9.1),
            "welfare": (8.0, 9.2),
            "pressure": (6.0, 7.8),
            "skills": [
                ("Linux / Shell Scripting", 4, 3.0, 1),
                ("Docker & Containerization", 3, 2.8, 1),
                ("CI/CD Pipelines (Jenkins / GitHub Actions)", 3, 2.5, 1),
                ("Kubernetes (K8s)", 2, 2.2, 0),
                ("AWS / Google Cloud / Azure", 3, 2.2, 0),
                ("Python", 3, 1.8, 0),
            ],
            "desc": "Vận hành hạ tầng Cloud, xây dựng đường ống CI/CD tự động hóa, giám sát Kubernetes cluster và tối ưu độ sẵn sàng hệ thống."
        },
        {
            "title": "Fresher Cybersecurity & Application Security Engineer",
            "major_code": "IT1",
            "level": "Fresher",
            "companies": ["Viettel", "Techcombank", "MB Bank", "CMC"],
            "salary_range": (13.0, 21.0),
            "min_gpa": 2.8,
            "min_eng": 4,
            "min_exp": 3,
            "work_modes": ["Onsite"],
            "training": (8.4, 9.3),
            "welfare": (8.2, 9.0),
            "pressure": (6.0, 7.8),
            "skills": [
                ("An toàn thông tin (Cybersecurity / Pentest)", 3, 3.0, 1),
                ("Linux / Shell Scripting", 3, 2.5, 1),
                ("Python", 3, 2.2, 1),
                ("Cấu trúc dữ liệu & Giải thuật", 3, 2.0, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4, 2.0, 0),
            ],
            "desc": "Đánh giá lỗ hổng bảo mật ứng dụng (Pentest), giám sát an ninh mạng SOC và bảo vệ hạ tầng số trọng yếu."
        },
        {
            "title": "Fresher Automation QA / Software Testing Engineer",
            "major_code": "IT2",
            "level": "Fresher",
            "companies": ["NashTech", "FPT Software", "Bosch VN", "MISA", "CMC"],
            "salary_range": (8.5, 14.0),
            "min_gpa": 2.5,
            "min_eng": 3,
            "min_exp": 0,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.2, 9.0),
            "welfare": (7.5, 8.8),
            "pressure": (4.0, 5.8),
            "skills": [
                ("Automated Testing / Selenium", 3, 3.0, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.5, 1),
                ("Python", 2, 2.0, 0),
                ("Java", 2, 2.0, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 3, 2.0, 1),
                ("Giải quyết vấn đề & Tư duy phản biện", 4, 1.8, 0),
            ],
            "desc": "Thiết kế kịch bản kiểm thử (Test Cases) và phát triển framework kiểm thử tự động cho ứng dụng Web/Mobile."
        },
        {
            "title": "Kỹ sư Cầu nối Nhật Bản Tập sự (Fresher BrSE / Japan IT)",
            "major_code": "IT2",
            "level": "Fresher",
            "companies": ["FPT Software", "Sun*", "CMC"],
            "salary_range": (14.0, 23.0),
            "min_gpa": 2.6,
            "min_eng": 3,
            "min_exp": 3,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (8.5, 9.3),
            "welfare": (8.0, 8.9),
            "pressure": (6.2, 7.8),
            "skills": [
                ("Tiếng Nhật (JLPT N3 / N2)", 4, 3.0, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.2, 1),
                ("Lập trình Hướng đối tượng (OOP)", 3, 2.2, 1),
                ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", 3, 2.0, 0),
                ("Làm việc nhóm & Giao tiếp Kỹ thuật", 4, 2.0, 0),
            ],
            "desc": "Làm cầu nối kỹ thuật giữa đội ngũ phát triển tại Việt Nam và khách hàng Nhật Bản, phân tích yêu cầu và quản lý chất lượng dự án."
        },

        # --- Nhóm DS1 / IT1: AI Engineer, Data Scientist, Data Engineer, BI Analyst ---
        {
            "title": "Fresher AI / Machine Learning Engineer (NLP & GenAI)",
            "major_code": "DS1",
            "level": "Fresher",
            "companies": ["VinBigdata", "FPT Smart Cloud", "Viettel", "VNG", "MoMo"],
            "salary_range": (14.0, 25.0),
            "min_gpa": 3.1,
            "min_eng": 4,
            "min_exp": 3,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.8, 9.6),
            "welfare": (8.2, 9.4),
            "pressure": (6.0, 7.8),
            "skills": [
                ("Python", 4, 3.0, 1),
                ("Deep Learning (PyTorch / TensorFlow)", 3, 3.0, 1),
                ("Xử lý Ngôn ngữ Tự nhiên (NLP / LLM / RAG)", 3, 2.8, 1),
                ("Machine Learning (Scikit-learn/XGBoost)", 4, 2.5, 1),
                ("MLOps (MLflow / Docker for AI)", 2, 1.8, 0),
                ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", 4, 1.8, 0),
            ],
            "desc": "Nghiên cứu và triển khai các mô hình Ngôn ngữ lớn (LLM), hệ thống RAG, Chatbot thông minh và trợ lý ảo tiếng Việt."
        },
        {
            "title": "Computer Vision & Edge AI Engineer",
            "major_code": "DS1",
            "level": "Fresher",
            "companies": ["Viettel High Tech", "VinBigdata", "Samsung R&D", "FPT Software"],
            "salary_range": (13.5, 22.0),
            "min_gpa": 3.0,
            "min_eng": 4,
            "min_exp": 3,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (8.5, 9.4),
            "welfare": (8.0, 9.1),
            "pressure": (5.8, 7.5),
            "skills": [
                ("Python", 4, 3.0, 1),
                ("Thị giác Máy tính (Computer Vision / OpenCV)", 4, 3.0, 1),
                ("Deep Learning (PyTorch / TensorFlow)", 3, 2.8, 1),
                ("C / C++", 3, 2.2, 0),
                ("Xác suất Thống kê & Tối ưu hóa", 3, 2.0, 0),
            ],
            "desc": "Phát triển thuật toán nhận diện khuôn mặt, OCR, nhận diện vật thể thời gian thực trên camera thông minh và thiết bị biên."
        },
        {
            "title": "Junior Data Scientist (Risk Modeling & Recommendation)",
            "major_code": "DS1",
            "level": "Junior",
            "companies": ["Techcombank", "Shopee VN", "MoMo", "One Mount", "MB Bank"],
            "salary_range": (15.0, 25.0),
            "min_gpa": 3.1,
            "min_eng": 4,
            "min_exp": 4,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.6, 9.5),
            "welfare": (8.5, 9.5),
            "pressure": (5.8, 7.5),
            "skills": [
                ("Python", 4, 3.0, 1),
                ("Machine Learning (Scikit-learn/XGBoost)", 4, 3.0, 1),
                ("SQL & Cơ sở dữ liệu", 4, 2.8, 1),
                ("Phân tích Dữ liệu (Pandas / NumPy)", 4, 2.5, 1),
                ("Xác suất Thống kê & Tối ưu hóa", 4, 2.5, 1),
                ("Phân tích Tài chính & Rủi ro (FinTech / Credit Scoring)", 2, 1.8, 0),
            ],
            "desc": "Xây dựng mô hình chấm điểm tín dụng (Credit Scoring), dự báo rời bỏ (Churn Prediction) và hệ thống gợi ý sản phẩm."
        },
        {
            "title": "Fresher Data Engineer (Big Data & ETL Pipeline)",
            "major_code": "DS1",
            "level": "Fresher",
            "companies": ["Viettel", "Techcombank", "One Mount", "NashTech", "VNG"],
            "salary_range": (13.0, 21.0),
            "min_gpa": 2.8,
            "min_eng": 3,
            "min_exp": 3,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.2, 9.2),
            "welfare": (8.0, 9.2),
            "pressure": (5.5, 7.2),
            "skills": [
                ("Python", 4, 3.0, 1),
                ("SQL & Cơ sở dữ liệu", 4, 3.0, 1),
                ("Apache Spark / Kafka / Airflow", 3, 2.8, 1),
                ("Data Warehouse (Snowflake / BigQuery)", 3, 2.4, 0),
                ("Docker & Containerization", 2, 1.8, 0),
                ("Linux / Shell Scripting", 3, 1.8, 0),
            ],
            "desc": "Thiết kế và vận hành đường ống dữ liệu lớn (ETL/ELT), xây dựng Data Lakehouse phục vụ phân tích BI và Machine Learning."
        },
        {
            "title": "Fresher Data Analyst / Business Intelligence (BI)",
            "major_code": "DS1",
            "level": "Fresher",
            "companies": ["Shopee VN", "MoMo", "MISA", "KPMG Vietnam", "Base.vn", "MB Bank"],
            "salary_range": (10.0, 16.5),
            "min_gpa": 2.7,
            "min_eng": 3,
            "min_exp": 2,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.0, 9.0),
            "welfare": (7.8, 9.0),
            "pressure": (4.8, 6.5),
            "skills": [
                ("SQL & Cơ sở dữ liệu", 4, 3.0, 1),
                ("Power BI / Tableau", 4, 2.8, 1),
                ("Phân tích Dữ liệu (Pandas / NumPy)", 3, 2.5, 1),
                ("Excel Nâng cao & VBA", 4, 2.0, 0),
                ("Thuyết trình & Viết báo cáo chuyên nghiệp", 4, 2.0, 0),
                ("Giải quyết vấn đề & Tư duy phản biện", 4, 2.0, 0),
            ],
            "desc": "Phân tích chỉ số vận hành kinh doanh, xây dựng hệ thống Dashboard Power BI/Tableau và đề xuất quyết định dựa trên dữ liệu."
        },

        # --- Nhóm EE1 / EE2 / ME1: Nhúng, Vi mạch, Tự động hóa, Cơ điện tử ---
        {
            "title": "Fresher Embedded Firmware Engineer (C/C++ & Automotive)",
            "major_code": "EE1",
            "level": "Fresher",
            "companies": ["Bosch VN", "LG R&D", "Samsung R&D", "FPT Software", "Viettel High Tech"],
            "salary_range": (11.5, 19.0),
            "min_gpa": 2.7,
            "min_eng": 3,
            "min_exp": 2,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (8.5, 9.4),
            "welfare": (8.0, 9.2),
            "pressure": (5.0, 6.8),
            "skills": [
                ("C / C++", 4, 3.0, 1),
                ("Vi điều khiển (STM32 / ARM / ESP32)", 3, 2.8, 1),
                ("RTOS / Embedded Linux", 3, 2.5, 1),
                ("Giao thức Công nghiệp (CAN / Modbus / MQTT)", 3, 2.2, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 3, 2.0, 1),
            ],
            "desc": "Phát triển phần mềm nhúng (Firmware, AUTOSAR, Infotainment) cho ô tô thông minh và thiết bị IoT công nghiệp."
        },
        {
            "title": "Fresher VLSI / IC Design & Verification Engineer",
            "major_code": "EE1",
            "level": "Fresher",
            "companies": ["Dolphin Tech", "FPT Semi", "Viettel High Tech", "Samsung R&D"],
            "salary_range": (13.0, 22.0),
            "min_gpa": 3.0,
            "min_eng": 4,
            "min_exp": 3,
            "work_modes": ["Onsite"],
            "training": (8.8, 9.5),
            "welfare": (8.2, 9.1),
            "pressure": (5.5, 7.2),
            "skills": [
                ("Thiết kế Vi mạch (Verilog / VHDL / FPGA)", 4, 3.0, 1),
                ("C / C++", 3, 2.5, 1),
                ("Linux / Shell Scripting", 3, 2.0, 1),
                ("Thiết kế Mạch PCB (Altium / OrCAD)", 2, 1.8, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4, 2.2, 1),
            ],
            "desc": "Thiết kế RTL, kiểm tra xác thực vi mạch số (ASIC/SoC Verification) và lập trình FPGA cho chip bán dẫn thế hệ mới."
        },
        {
            "title": "Hardware & IoT Circuit Design Engineer",
            "major_code": "EE1",
            "level": "Fresher",
            "companies": ["Viettel High Tech", "Bosch VN", "Canon VN"],
            "salary_range": (11.0, 17.5),
            "min_gpa": 2.7,
            "min_eng": 3,
            "min_exp": 2,
            "work_modes": ["Onsite"],
            "training": (8.0, 9.0),
            "welfare": (7.8, 8.8),
            "pressure": (5.2, 6.8),
            "skills": [
                ("Thiết kế Mạch PCB (Altium / OrCAD)", 4, 3.0, 1),
                ("Vi điều khiển (STM32 / ARM / ESP32)", 3, 2.6, 1),
                ("C / C++", 3, 2.2, 1),
                ("MATLAB / Simulink", 3, 1.8, 0),
            ],
            "desc": "Thiết kế sơ đồ nguyên lý, layout mạch PCB nhiều lớp và đo kiểm phần cứng cho thiết bị viễn thông 5G và IoT."
        },
        {
            "title": "Kỹ sư Tự động hóa & Điều khiển Công nghiệp (PLC / SCADA)",
            "major_code": "EE2",
            "level": "Fresher",
            "companies": ["Siemens", "ABB Vietnam", "Canon VN", "Bosch VN"],
            "salary_range": (11.0, 18.5),
            "min_gpa": 2.7,
            "min_eng": 3,
            "min_exp": 2,
            "work_modes": ["Onsite"],
            "training": (8.5, 9.4),
            "welfare": (8.2, 9.3),
            "pressure": (4.8, 6.5),
            "skills": [
                ("PLC / SCADA / HMI (Siemens / Mitsubishi)", 4, 3.0, 1),
                ("Giao thức Công nghiệp (CAN / Modbus / MQTT)", 3, 2.5, 1),
                ("MATLAB / Simulink", 3, 2.2, 0),
                ("Thiết kế Mạch PCB (Altium / OrCAD)", 2, 1.8, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 3, 2.0, 1),
            ],
            "desc": "Lập trình PLC Siemens/ABB, thiết kế giao diện giám sát SCADA và triển khai giải pháp nhà máy thông minh (Smart Factory)."
        },
        {
            "title": "Kỹ sư Robot & Hệ thống Điều khiển Chuyển động (Robotics)",
            "major_code": "EE2",
            "level": "Fresher",
            "companies": ["ABB Vietnam", "Viettel High Tech", "VinBigdata", "Samsung R&D"],
            "salary_range": (12.5, 20.5),
            "min_gpa": 2.9,
            "min_eng": 4,
            "min_exp": 3,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (8.4, 9.3),
            "welfare": (8.0, 9.0),
            "pressure": (5.5, 7.0),
            "skills": [
                ("ROS / Robot Điều khiển Chuyển động", 3, 3.0, 1),
                ("C / C++", 3, 2.8, 1),
                ("Python", 3, 2.4, 1),
                ("MATLAB / Simulink", 3, 2.2, 0),
                ("PLC / SCADA / HMI (Siemens / Mitsubishi)", 3, 2.0, 0),
            ],
            "desc": "Nghiên cứu điều khiển robot tự hành AGV/AMR, cánh tay robot công nghiệp và tích hợp cảm biến thông minh."
        },
        {
            "title": "Kỹ sư Thiết kế Cơ điện tử & Tự động hóa Sản xuất (R&D Mechatronics)",
            "major_code": "ME1",
            "level": "Fresher",
            "companies": ["Canon VN", "ABB Vietnam", "Samsung R&D", "Siemens", "Viettel High Tech"],
            "salary_range": (10.5, 17.5),
            "min_gpa": 2.6,
            "min_eng": 3,
            "min_exp": 2,
            "work_modes": ["Onsite"],
            "training": (8.0, 9.1),
            "welfare": (7.8, 9.0),
            "pressure": (5.0, 6.8),
            "skills": [
                ("CAD / CAM / SolidWorks / AutoCAD", 4, 3.0, 1),
                ("PLC / SCADA / HMI (Siemens / Mitsubishi)", 3, 2.5, 1),
                ("ROS / Robot Điều khiển Chuyển động", 2, 2.0, 0),
                ("C / C++", 2, 1.8, 0),
                ("Giải quyết vấn đề & Tư duy phản biện", 4, 2.0, 0),
            ],
            "desc": "Thiết kế mô hình cơ khí 3D trên SolidWorks, tích hợp cơ cấu chấp hành điện - khí nén và dây chuyền lắp ráp tự động."
        },

        # --- Nhóm EM1 / EM2: Business Analyst, Product Owner, ERP Consultant, FinTech/Supply Chain ---
        {
            "title": "Fresher IT Business Analyst (IT BA - Banking & Enterprise)",
            "major_code": "EM1",
            "level": "Fresher",
            "companies": ["Techcombank", "MB Bank", "MISA", "FPT Software", "CMC", "One Mount"],
            "salary_range": (10.5, 17.5),
            "min_gpa": 2.8,
            "min_eng": 4,
            "min_exp": 2,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.2, 9.2),
            "welfare": (8.0, 9.2),
            "pressure": (5.2, 7.0),
            "skills": [
                ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", 4, 3.0, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.6, 1),
                ("Quản lý Sản phẩm (Product Management / Agile Scrum)", 3, 2.2, 0),
                ("UI/UX Design & Figma Prototyping", 3, 2.0, 0),
                ("Thuyết trình & Viết báo cáo chuyên nghiệp", 4, 2.4, 1),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4, 2.2, 1),
            ],
            "desc": "Khảo sát yêu cầu người dùng, mô hình hóa quy trình BPMN/UML, viết tài liệu SRS/User Story và phối hợp cùng đội ngũ kỹ sư."
        },
        {
            "title": "Fresher ERP Functional Consultant (SAP / Odoo)",
            "major_code": "EM1",
            "level": "Fresher",
            "companies": ["KPMG Vietnam", "FPT Software", "MISA", "CMC"],
            "salary_range": (10.0, 16.5),
            "min_gpa": 2.7,
            "min_eng": 4,
            "min_exp": 2,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (8.5, 9.3),
            "welfare": (7.8, 8.9),
            "pressure": (5.5, 7.2),
            "skills": [
                ("Hệ thống ERP (SAP / Odoo)", 3, 3.0, 1),
                ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", 3, 2.8, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.2, 1),
                ("Excel Nâng cao & VBA", 4, 2.0, 0),
                ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", 3, 2.0, 0),
            ],
            "desc": "Tư vấn triển khai các phân hệ ERP (Tài chính kế toán, Mua hàng, Kho vận, Sản xuất) cho doanh nghiệp lớn."
        },
        {
            "title": "Associate Product Manager / Management Trainee (Tech Product)",
            "major_code": "EM2",
            "level": "Management Trainee",
            "companies": ["Shopee VN", "VNG", "MoMo", "Base.vn", "One Mount"],
            "salary_range": (14.0, 23.0),
            "min_gpa": 3.2,
            "min_eng": 5,
            "min_exp": 3,
            "work_modes": ["Hybrid", "Onsite"],
            "training": (9.0, 9.7),
            "welfare": (8.6, 9.5),
            "pressure": (6.5, 8.2),
            "skills": [
                ("Quản lý Sản phẩm (Product Management / Agile Scrum)", 4, 3.0, 1),
                ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", 3, 2.5, 1),
                ("Power BI / Tableau", 3, 2.2, 0),
                ("Digital Marketing & Growth Analytics", 3, 2.2, 0),
                ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", 4, 2.8, 1),
                ("Giải quyết vấn đề & Tư duy phản biện", 4, 2.5, 1),
            ],
            "desc": "Chương trình Quản trị viên tập sự phát triển sản phẩm công nghệ, điều phối chiến lược tăng trưởng người dùng và tối ưu tính năng."
        },
        {
            "title": "Supply Chain & Operations Data Analyst",
            "major_code": "EM2",
            "level": "Fresher",
            "companies": ["Shopee VN", "Canon VN", "One Mount", "Bosch VN"],
            "salary_range": (10.0, 16.0),
            "min_gpa": 2.7,
            "min_eng": 4,
            "min_exp": 2,
            "work_modes": ["Onsite", "Hybrid"],
            "training": (8.0, 9.0),
            "welfare": (8.0, 9.0),
            "pressure": (5.0, 6.8),
            "skills": [
                ("Quản trị Chuỗi cung ứng & Logistics (Supply Chain)", 4, 3.0, 1),
                ("Excel Nâng cao & VBA", 4, 2.8, 1),
                ("Power BI / Tableau", 3, 2.4, 1),
                ("SQL & Cơ sở dữ liệu", 3, 2.2, 0),
                ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4, 2.0, 1),
            ],
            "desc": "Phân tích dữ liệu vận hành chuỗi cung ứng, tối ưu hóa luồng hàng hóa, dự báo tồn kho và chi phí logistics."
        },
    ]

    # Bản đồ khoảng cách ước tính từ khu vực Bách Khoa (Hai Bà Trưng) đến các quận tại Hà Nội
    district_distance_map = {
        "Hai Bà Trưng (Times City)": 3.2,
        "Hai Bà Trưng": 2.0,
        "Hoàn Kiếm": 3.8,
        "Đống Đa": 4.2,
        "Ba Đình": 5.5,
        "Hoàng Mai / Bắc Ninh": 6.5,
        "Cầu Giấy": 8.5,
        "Cầu Giấy / Hòa Lạc": 9.5,
        "Nam Từ Liêm": 10.2,
        "Nam Từ Liêm (Keangnam)": 9.8,
        "Long Biên": 8.0,
        "Bắc Từ Liêm (Tây Hồ Tây)": 11.0,
        "Đông Anh (KCN Bắc Thăng Long)": 18.5,
        "Thạch Thất (Hòa Lạc) / Cầu Giấy": 14.0,
    }

    jobs_data = []
    job_counter = 1
    rng = random.Random(2026)

    for tpl in job_templates:
        for idx, comp_short in enumerate(tpl["companies"]):
            # Bổ sung biến thể thực tập / fresher / junior để đạt >105 việc làm đa dạng
            levels_to_create = [tpl["level"]]
            if idx == 0 and tpl["level"] == "Fresher":
                levels_to_create.append("Junior")
            elif idx == 1 and tpl["level"] == "Fresher":
                levels_to_create.append("Intern")

            for lv in levels_to_create:
                sal_min, sal_max = tpl["salary_range"]
                min_gpa = tpl["min_gpa"]
                min_eng = tpl["min_eng"]
                min_exp = tpl["min_exp"]

                if lv == "Intern":
                    sal_min = round(max(4.0, sal_min * 0.45), 1)
                    sal_max = round(max(7.0, sal_max * 0.50), 1)
                    min_gpa = round(max(2.3, min_gpa - 0.2), 2)
                    min_exp = 0
                elif lv == "Junior":
                    sal_min = round(sal_min * 1.25 + rng.uniform(-0.5, 1.0), 1)
                    sal_max = round(sal_max * 1.30 + rng.uniform(0.0, 1.5), 1)
                    min_gpa = round(min(3.4, min_gpa + 0.1), 2)
                    min_exp = max(6, min_exp + 3)
                else:
                    sal_min = round(sal_min + rng.uniform(-0.8, 1.2), 1)
                    sal_max = round(sal_max + rng.uniform(-0.5, 1.8), 1)

                title = tpl["title"]
                if lv == "Intern":
                    title = title.replace("Fresher", "Thực tập sinh Tài năng (Intern)").replace("Junior", "Intern")
                elif lv == "Junior" and "Fresher" in title:
                    title = title.replace("Fresher", "Junior")

                work_mode = tpl["work_modes"][idx % len(tpl["work_modes"])]
                training_score = round(rng.uniform(*tpl["training"]), 1)
                welfare_score = round(rng.uniform(*tpl["welfare"]), 1)
                pressure_score = round(rng.uniform(*tpl["pressure"]), 1)

                job_code = f"JOB-{job_counter:03d}"
                job_counter += 1

                jobs_data.append({
                    "job_code": job_code,
                    "company_short": comp_short,
                    "major_code": tpl["major_code"],
                    "title": f"{title} - {comp_short}",
                    "level": lv,
                    "salary_min": sal_min,
                    "salary_max": sal_max,
                    "min_gpa": min_gpa,
                    "min_english_tier": min_eng,
                    "min_exp_months": min_exp,
                    "work_mode": work_mode,
                    "training_score": training_score,
                    "welfare_score": welfare_score,
                    "overtime_pressure_score": pressure_score,
                    "slots": rng.randint(2, 8),
                    "description": tpl["desc"],
                    "benefits_summary": "Lương tháng 13-15, thưởng hiệu quả dự án, bảo hiểm sức khỏe cao cấp, lộ trình Mentorship 1-1 cho SV mới tốt nghiệp.",
                    "skills": tpl["skills"],
                    "district_distance_map": district_distance_map,
                })

    return jobs_data


# 5. Danh sách 10 Hồ sơ Sinh viên Tốt nghiệp Mẫu (Đa dạng ngành, GPA, Kỹ năng & Định hướng)
STUDENT_PROFILES = [
    {
        "student_code": "20215001",
        "full_name": "Nguyễn Minh Quân (CNTT - Định hướng AI/Data)",
        "major_code": "DS1",
        "gpa": 3.45,
        "english_tier": 5,
        "english_cert": "IELTS 7.0",
        "internship_months": 6,
        "min_expected_salary": 13.0,
        "preferred_city": "Hà Nội",
        "current_district": "Hai Bà Trưng",
        "max_distance_km": 14.0,
        "preferred_work_mode": "Any",
        "career_goal": "Trở thành AI / Machine Learning Engineer hoặc Data Scientist tại các công ty công nghệ lớn có bài toán dữ liệu thực tế.",
        "persona_preset": "growth_focused",
        "skills": [
            ("Python", 5),
            ("Machine Learning (Scikit-learn/XGBoost)", 4),
            ("Deep Learning (PyTorch / TensorFlow)", 4),
            ("Xử lý Ngôn ngữ Tự nhiên (NLP / LLM / RAG)", 4),
            ("Phân tích Dữ liệu (Pandas / NumPy)", 5),
            ("SQL & Cơ sở dữ liệu", 4),
            ("Xác suất Thống kê & Tối ưu hóa", 4),
            ("Docker & Containerization", 3),
            ("Git / GitHub / GitLab CI", 4),
            ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", 4),
            ("Khả năng tự học công nghệ mới", 5),
        ],
    },
    {
        "student_code": "20215108",
        "full_name": "Trần Hoàng Nam (Kỹ thuật Phần mềm - Backend Java/Go)",
        "major_code": "IT2",
        "gpa": 3.18,
        "english_tier": 4,
        "english_cert": "TOEIC 750",
        "internship_months": 5,
        "min_expected_salary": 12.0,
        "preferred_city": "Hà Nội",
        "current_district": "Đống Đa",
        "max_distance_km": 12.0,
        "preferred_work_mode": "Any",
        "career_goal": "Phát triển hệ thống Backend Microservices chịu tải cao tại các ngân hàng số hoặc tập đoàn công nghệ.",
        "persona_preset": "income_focused",
        "skills": [
            ("Java", 4),
            ("Spring Boot", 4),
            ("Golang", 3),
            ("SQL & Cơ sở dữ liệu", 4),
            ("Cấu trúc dữ liệu & Giải thuật", 4),
            ("Lập trình Hướng đối tượng (OOP)", 4),
            ("RESTful API / GraphQL", 4),
            ("Docker & Containerization", 3),
            ("Redis / Elasticsearch / Message Queue", 3),
            ("Git / GitHub / GitLab CI", 4),
            ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4),
        ],
    },
    {
        "student_code": "20215234",
        "full_name": "Lê Thu Hà (CNTT - Fullstack Web React/Node.js)",
        "major_code": "IT2",
        "gpa": 2.95,
        "english_tier": 4,
        "english_cert": "TOEIC 680",
        "internship_months": 4,
        "min_expected_salary": 10.0,
        "preferred_city": "Hà Nội",
        "current_district": "Cầu Giấy",
        "max_distance_km": 10.0,
        "preferred_work_mode": "Hybrid",
        "career_goal": "Làm việc ở môi trường trẻ trung, cân bằng cuộc sống, phát triển sản phẩm Web Frontend/Fullstack với React & TypeScript.",
        "persona_preset": "work_life_balance",
        "skills": [
            ("JavaScript / TypeScript", 4),
            ("React.js / Next.js", 4),
            ("HTML5 / CSS3 / Tailwind", 5),
            ("Node.js / Express / NestJS", 3),
            ("RESTful API / GraphQL", 4),
            ("SQL & Cơ sở dữ liệu", 3),
            ("UI/UX Design & Figma Prototyping", 3),
            ("Git / GitHub / GitLab CI", 4),
            ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4),
            ("Làm việc nhóm & Giao tiếp Kỹ thuật", 4),
        ],
    },
    {
        "student_code": "20215312",
        "full_name": "Phạm Đức Anh (CNTT Việt-Nhật HEDSPI - Định hướng BrSE)",
        "major_code": "IT2",
        "gpa": 3.05,
        "english_tier": 3,
        "english_cert": "JLPT N2 & TOEIC 600",
        "internship_months": 4,
        "min_expected_salary": 13.0,
        "preferred_city": "Hà Nội",
        "current_district": "Nam Từ Liêm",
        "max_distance_km": 15.0,
        "preferred_work_mode": "Any",
        "career_goal": "Phát triển sự nghiệp Kỹ sư cầu nối (BrSE) hoặc Kỹ sư phần mềm thị trường Nhật Bản.",
        "persona_preset": "income_focused",
        "skills": [
            ("Tiếng Nhật (JLPT N3 / N2)", 5),
            ("Java", 3),
            ("JavaScript / TypeScript", 3),
            ("SQL & Cơ sở dữ liệu", 4),
            ("Lập trình Hướng đối tượng (OOP)", 4),
            ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", 4),
            ("Làm việc nhóm & Giao tiếp Kỹ thuật", 4),
            ("Git / GitHub / GitLab CI", 3),
        ],
    },
    {
        "student_code": "20213045",
        "full_name": "Vũ Quốc Khánh (Điện tử Viễn thông - Nhúng & Vi mạch VLSI)",
        "major_code": "EE1",
        "gpa": 3.32,
        "english_tier": 4,
        "english_cert": "TOEIC 730",
        "internship_months": 4,
        "min_expected_salary": 12.0,
        "preferred_city": "Hà Nội",
        "current_district": "Hai Bà Trưng",
        "max_distance_km": 15.0,
        "preferred_work_mode": "Onsite",
        "career_goal": "Nghiên cứu thiết kế vi mạch bán dẫn (VLSI/FPGA) hoặc lập trình nhúng Firmware tại các trung tâm R&D lớn.",
        "persona_preset": "skill_fit_focused",
        "skills": [
            ("C / C++", 4),
            ("Thiết kế Vi mạch (Verilog / VHDL / FPGA)", 4),
            ("Vi điều khiển (STM32 / ARM / ESP32)", 4),
            ("RTOS / Embedded Linux", 3),
            ("Thiết kế Mạch PCB (Altium / OrCAD)", 4),
            ("Linux / Shell Scripting", 3),
            ("Giao thức Công nghiệp (CAN / Modbus / MQTT)", 3),
            ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 4),
        ],
    },
    {
        "student_code": "20213290",
        "full_name": "Đặng Quang Huy (Điều khiển & Tự động hóa - PLC/Robotics)",
        "major_code": "EE2",
        "gpa": 3.10,
        "english_tier": 3,
        "english_cert": "TOEIC 620",
        "internship_months": 3,
        "min_expected_salary": 10.5,
        "preferred_city": "Hà Nội",
        "current_district": "Hoàng Mai",
        "max_distance_km": 18.0,
        "preferred_work_mode": "Onsite",
        "career_goal": "Kỹ sư tự động hóa nhà máy thông minh, lập trình PLC/SCADA và điều khiển Robot công nghiệp.",
        "persona_preset": "balanced",
        "skills": [
            ("PLC / SCADA / HMI (Siemens / Mitsubishi)", 4),
            ("Giao thức Công nghiệp (CAN / Modbus / MQTT)", 4),
            ("ROS / Robot Điều khiển Chuyển động", 3),
            ("MATLAB / Simulink", 4),
            ("C / C++", 3),
            ("Python", 3),
            ("Thiết kế Mạch PCB (Altium / OrCAD)", 3),
            ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 3),
        ],
    },
    {
        "student_code": "20216019",
        "full_name": "Hoàng Gia Bảo (Kỹ thuật Cơ điện tử - CAD/CAM & Robot)",
        "major_code": "ME1",
        "gpa": 2.88,
        "english_tier": 3,
        "english_cert": "TOEIC 580",
        "internship_months": 3,
        "min_expected_salary": 10.0,
        "preferred_city": "Hà Nội",
        "current_district": "Đống Đa",
        "max_distance_km": 20.0,
        "preferred_work_mode": "Onsite",
        "career_goal": "Thiết kế hệ thống cơ điện tử, máy tự động hóa sản xuất tại các tập đoàn FDI Nhật Bản / Châu Âu.",
        "persona_preset": "balanced",
        "skills": [
            ("CAD / CAM / SolidWorks / AutoCAD", 5),
            ("PLC / SCADA / HMI (Siemens / Mitsubishi)", 3),
            ("ROS / Robot Điều khiển Chuyển động", 3),
            ("Vi điều khiển (STM32 / ARM / ESP32)", 3),
            ("C / C++", 3),
            ("Giải quyết vấn đề & Tư duy phản biện", 4),
            ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 3),
        ],
    },
    {
        "student_code": "20214115",
        "full_name": "Ngô Phương Linh (Hệ thống Thông tin Quản lý - IT BA / Data Analyst)",
        "major_code": "EM1",
        "gpa": 3.52,
        "english_tier": 5,
        "english_cert": "IELTS 7.0",
        "internship_months": 5,
        "min_expected_salary": 11.0,
        "preferred_city": "Hà Nội",
        "current_district": "Ba Đình",
        "max_distance_km": 12.0,
        "preferred_work_mode": "Hybrid",
        "career_goal": "Trở thành IT Business Analyst hoặc Product Owner trong lĩnh vực Ngân hàng số, FinTech hoặc Tư vấn ERP.",
        "persona_preset": "growth_focused",
        "skills": [
            ("Phân tích Nghiệp vụ (Business Analysis / UML / BPMN)", 5),
            ("Quản lý Sản phẩm (Product Management / Agile Scrum)", 4),
            ("SQL & Cơ sở dữ liệu", 4),
            ("Power BI / Tableau", 4),
            ("UI/UX Design & Figma Prototyping", 4),
            ("Hệ thống ERP (SAP / Odoo)", 3),
            ("Excel Nâng cao & VBA", 4),
            ("Thuyết trình & Viết báo cáo chuyên nghiệp", 5),
            ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", 5),
        ],
    },
    {
        "student_code": "20214288",
        "full_name": "Bùi Tuấn Kiệt (Kinh tế Công nghệ - Product & Supply Chain Analytics)",
        "major_code": "EM2",
        "gpa": 3.25,
        "english_tier": 5,
        "english_cert": "IELTS 6.5",
        "internship_months": 4,
        "min_expected_salary": 11.0,
        "preferred_city": "Hà Nội",
        "current_district": "Hai Bà Trưng",
        "max_distance_km": 14.0,
        "preferred_work_mode": "Any",
        "career_goal": "Ứng tuyển Management Trainee hoặc Chuyên viên phân tích vận hành / phát triển sản phẩm thương mại điện tử.",
        "persona_preset": "growth_focused",
        "skills": [
            ("Quản trị Chuỗi cung ứng & Logistics (Supply Chain)", 4),
            ("Quản lý Sản phẩm (Product Management / Agile Scrum)", 4),
            ("Power BI / Tableau", 4),
            ("SQL & Cơ sở dữ liệu", 3),
            ("Excel Nâng cao & VBA", 5),
            ("Digital Marketing & Growth Analytics", 4),
            ("Tiếng Anh Thương mại & Thuyết trình (IELTS 6.5+)", 4),
            ("Giải quyết vấn đề & Tư duy phản biện", 4),
        ],
    },
    {
        "student_code": "20215499",
        "full_name": "Đỗ Mai Anh (CNTT - Fresher QA/Tester & Python cơ bản)",
        "major_code": "IT2",
        "gpa": 2.68,
        "english_tier": 3,
        "english_cert": "TOEIC 560",
        "internship_months": 2,
        "min_expected_salary": 8.0,
        "preferred_city": "Hà Nội",
        "current_district": "Cầu Giấy",
        "max_distance_km": 12.0,
        "preferred_work_mode": "Hybrid",
        "career_goal": "Tìm kiếm vị trí Fresher Automation/Manual QA hoặc Thực tập sinh có lộ trình đào tạo bài bản, ít áp lực OT.",
        "persona_preset": "work_life_balance",
        "skills": [
            ("Automated Testing / Selenium", 3),
            ("SQL & Cơ sở dữ liệu", 3),
            ("Python", 3),
            ("HTML5 / CSS3 / Tailwind", 3),
            ("Tiếng Anh Giao tiếp & Đọc hiểu Tài liệu", 3),
            ("Giải quyết vấn đề & Tư duy phản biện", 4),
            ("Làm việc nhóm & Giao tiếp Kỹ thuật", 4),
        ],
    },
]


def init_database(force_recreate=True):
    """Khởi tạo CSDL SQLite và nạp toàn bộ dữ liệu mẫu."""
    if force_recreate and DB_PATH.exists():
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cur.executescript(schema_sql)

    # 1. Insert Majors
    major_id_map = {}
    for code, name, faculty, desc in MAJORS:
        cur.execute(
            "INSERT INTO majors (code, name, faculty, description) VALUES (?, ?, ?, ?)",
            (code, name, faculty, desc),
        )
        major_id_map[code] = cur.lastrowid

    # 2. Insert Skills
    skill_id_map = {}
    for name, cat, desc in SKILLS:
        cur.execute(
            "INSERT INTO skills (name, category, description) VALUES (?, ?, ?)",
            (name, cat, desc),
        )
        skill_id_map[name] = cur.lastrowid

    # 3. Insert Companies
    company_map = {}
    for name, short_name, industry, size_tier, rating, district, city, website, desc in COMPANIES:
        cur.execute(
            """
            INSERT INTO companies
            (name, short_name, industry, size_tier, rating, headquarters_district, city, website, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, short_name, industry, size_tier, rating, district, city, website, desc),
        )
        company_map[short_name] = {
            "id": cur.lastrowid,
            "district": district,
            "city": city,
        }

    # 4. Insert Criteria
    for code, name, short_name, ctype, unit, def_w, desc, f_note in CRITERIA:
        cur.execute(
            """
            INSERT INTO criteria
            (code, name, short_name, type, unit, default_weight, description, formula_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (code, name, short_name, ctype, unit, def_w, desc, f_note),
        )

    # 5. Insert Jobs & Job Skills
    jobs_catalog = build_jobs_catalog()
    total_job_skills = 0
    for j in jobs_catalog:
        comp_info = company_map[j["company_short"]]
        dist_km = j["district_distance_map"].get(comp_info["district"], 8.5)
        cur.execute(
            """
            INSERT INTO jobs (
                job_code, company_id, target_major_id, title, level,
                salary_min, salary_max, min_gpa, min_english_tier, min_exp_months,
                district, city, distance_km_from_center, work_mode,
                training_score, welfare_score, overtime_pressure_score,
                slots, description, benefits_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                j["job_code"],
                comp_info["id"],
                major_id_map[j["major_code"]],
                j["title"],
                j["level"],
                j["salary_min"],
                j["salary_max"],
                j["min_gpa"],
                j["min_english_tier"],
                j["min_exp_months"],
                comp_info["district"],
                comp_info["city"],
                dist_km,
                j["work_mode"],
                j["training_score"],
                j["welfare_score"],
                j["overtime_pressure_score"],
                j["slots"],
                j["description"],
                j["benefits_summary"],
            ),
        )
        job_id = cur.lastrowid

        for s_name, req_lv, imp_w, is_mand in j["skills"]:
            if j["level"] == "Intern":
                req_lv = max(1, req_lv - 1)
            elif j["level"] == "Junior":
                req_lv = min(5, req_lv + 1)
            cur.execute(
                """
                INSERT INTO job_skills (job_id, skill_id, required_level, importance_weight, is_mandatory)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, skill_id_map[s_name], req_lv, imp_w, is_mand),
            )
            total_job_skills += 1

    # 6. Insert Student Profiles & Student Skills
    total_student_skills = 0
    for sp in STUDENT_PROFILES:
        cur.execute(
            """
            INSERT INTO student_profiles (
                student_code, full_name, major_id, gpa, english_tier, english_cert,
                internship_months, min_expected_salary, preferred_city, current_district,
                max_distance_km, preferred_work_mode, career_goal, persona_preset
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sp["student_code"],
                sp["full_name"],
                major_id_map[sp["major_code"]],
                sp["gpa"],
                sp["english_tier"],
                sp["english_cert"],
                sp["internship_months"],
                sp["min_expected_salary"],
                sp["preferred_city"],
                sp["current_district"],
                sp["max_distance_km"],
                sp["preferred_work_mode"],
                sp["career_goal"],
                sp["persona_preset"],
            ),
        )
        st_id = cur.lastrowid
        for s_name, prof_lv in sp["skills"]:
            cur.execute(
                """
                INSERT INTO student_skills (student_id, skill_id, proficiency_level)
                VALUES (?, ?, ?)
                """,
                (st_id, skill_id_map[s_name], prof_lv),
            )
            total_student_skills += 1

    conn.commit()

    summary = {
        "database_path": str(DB_PATH),
        "majors_count": len(MAJORS),
        "skills_count": len(SKILLS),
        "companies_count": len(COMPANIES),
        "criteria_count": len(CRITERIA),
        "jobs_count": len(jobs_catalog),
        "job_skills_relations": total_job_skills,
        "student_profiles_count": len(STUDENT_PROFILES),
        "student_skills_relations": total_student_skills,
    }

    with open(SEED_EXPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    conn.close()
    return summary


if __name__ == "__main__":
    stats = init_database(force_recreate=True)
    print("=== KHỞI TẠO CƠ SỞ DỮ LIỆU DSS THÀNH CÔNG ===")
    for k, v in stats.items():
        print(f" - {k}: {v}")


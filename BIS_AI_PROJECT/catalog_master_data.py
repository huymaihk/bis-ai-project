"""
BIS Textile AI - Verified Catalog Master Data
=============================================
Được đối soát 100% từ catalogue_sample.pdf gốc.
Khắc phục triệt để tình trạng gộp nhầm tên sản phẩm giữa các mã SKU trên cùng một trang PDF.
"""

CATALOG_MASTER = {
    # Page 7
    "03026A": {
        "en": "AATCC MANUAL OF INTERNATIONAL TEST METHODS AND PROCEDURES (Hardbound Book)",
        "vi": "Sổ tay Phương pháp Thử nghiệm & Quy trình Quốc tế AATCC (Bìa cứng)",
        "desc": "Sổ tay biên soạn các phương pháp thử nghiệm, quy trình phòng thí nghiệm, quy trình đánh giá và chuyên khảo do các Ủy ban Nghiên cứu AATCC phát triển. Xuất bản thường niên, ấn bản kỷ niệm lần thứ 100.",
        "scope": "Tiêu chuẩn phương pháp thử nghiệm dệt may quốc tế AATCC",
        "doc": "Sổ tay Phương pháp thử nghiệm Quốc tế AATCC",
        "page": "7"
    },
    "03026B": {
        "en": "AATCC MANUAL OF INTERNATIONAL TEST METHODS AND PROCEDURES (PDF Download)",
        "vi": "Sổ tay Phương pháp Thử nghiệm & Quy trình Quốc tế AATCC (Bản điện tử PDF)",
        "desc": "Phiên bản điện tử PDF tải về của Sổ tay Phương pháp Thử nghiệm và Quy trình Quốc tế AATCC. Bao gồm toàn bộ phương pháp thử, quy trình thực hành phòng lab QA/QC dệt may.",
        "scope": "Tiêu chuẩn phương pháp thử nghiệm dệt may quốc tế AATCC",
        "doc": "Sổ tay Phương pháp thử nghiệm Quốc tế AATCC",
        "page": "7"
    },
    "03017C": {
        "en": "ASTM COMPASS ONLINE SUBSCRIPTION - AATCC COLLECTION",
        "vi": "Gói thuê bao trực tuyến tiêu chuẩn AATCC qua ASTM Compass®",
        "desc": "Truy cập trực tuyến cơ sở dữ liệu ASTM Compass bao gồm toàn bộ tài liệu trong Sổ tay Phương pháp thử nghiệm AATCC hiện hành, các tiêu chuẩn lịch sử và phụ lục kỹ thuật.",
        "scope": "Tra cứu tiêu chuẩn thử nghiệm trực tuyến toàn cầu",
        "doc": "Hệ thống cơ sở dữ liệu ASTM Compass®",
        "page": "7"
    },

    # Page 8
    "03000A": {
        "en": "TECHNICAL SUPPLEMENT",
        "vi": "Tài liệu Phụ lục Kỹ thuật Thực hành Dệt may (Technical Supplement)",
        "desc": "Tập hợp các tài liệu hướng dẫn và thực hành ngành dệt may dành cho sản phẩm dệt may dạng PDF tải về. Xuất bản năm 2004.",
        "scope": "Hướng dẫn thực hành kỹ thuật dệt may",
        "doc": "AATCC Technical Supplement",
        "page": "8"
    },
    "03001A": {
        "en": "MOISTURE MANAGEMENT TECHNICAL SUPPLEMENT",
        "vi": "Phụ lục Kỹ thuật Quản lý Độ ẩm Dệt may (Moisture Management Supplement)",
        "desc": "Tập hợp các tài liệu hướng dẫn và tiêu chuẩn nội bộ ngành về đánh giá quản lý độ ẩm, truyền dẫn mồ hôi của vải dạng PDF tải về. Xuất bản năm 2008.",
        "scope": "Phương pháp kiểm tra tính năng quản lý độ ẩm của vải",
        "doc": "AATCC Moisture Management Technical Supplement",
        "page": "8"
    },
    "03003A": {
        "en": "FIBER IDENTIFICATION SUPPLEMENT",
        "vi": "Phụ lục Kỹ thuật Định tính & Nhận dạng Xơ sợi (Fiber Identification)",
        "desc": "Tài liệu chuyên khảo hỗ trợ phương pháp AATCC TM20 & TM20A bao gồm ảnh hiển vi màu phân cực, đường cong phổ hồng ngoại FTIR và kỹ thuật kiểm nghiệm xơ sợi phòng lab.",
        "scope": "Nhận dạng và phân tích định tính xơ sợi dệt may",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM20 / TM20A",
        "page": "8"
    },
    "09615A": {
        "en": "TEXTILE DYEING AND COLORATION (Hardbound)",
        "vi": "Sách Chuyên khảo Nhuộm và Tạo màu Dệt may (Bìa cứng)",
        "desc": "Tài liệu chuyên khảo bao quát cấu trúc và ứng dụng của các loại thuốc nhuộm trong công nghiệp dệt may của tác giả J. Richard Aspland. Bìa cứng, xuất bản năm 1997.",
        "scope": "Kỹ thuật nhuộm và hóa chất dệt may",
        "doc": "Giáo trình Nhuộm & Phối màu Dệt may AATCC",
        "page": "8"
    },

    # Page 9
    "09616A": {
        "en": "TEXTILE COLORATION FOR THE RETAIL SUPPLY CHAIN",
        "vi": "Sách Tạo màu Dệt may trong Chuỗi cung ứng Bán lẻ",
        "desc": "Tài liệu hướng dẫn thực tế về quản lý và kiểm soát màu sắc nhuộm/in cho các chuyên gia màu sắc, nhà thiết kế, thu mua và merchandiser trong chuỗi cung ứng dệt may.",
        "scope": "Quản lý màu sắc dệt may bán lẻ",
        "doc": "Tài liệu Chuỗi cung ứng Dệt may AATCC",
        "page": "9"
    },
    "03004A": {
        "en": "COLOR GUIDEBOOK (Individual License)",
        "vi": "Sổ tay Hướng dẫn Quản lý Màu sắc (Bản quyền Cá nhân)",
        "desc": "Hướng dẫn chi tiết quản lý chương trình kiểm soát màu sắc trong phòng lab và nhà máy dệt may, kèm các phụ lục biểu mẫu có thể chỉnh sửa dạng PDF bản quyền cá nhân.",
        "scope": "Kiểm soát và đánh giá màu sắc dệt may",
        "doc": "AATCC Color Guidebook",
        "page": "9"
    },
    "03004B": {
        "en": "COLOR GUIDEBOOK (Corporate License)",
        "vi": "Sổ tay Hướng dẫn Quản lý Màu sắc (Bản quyền Doanh nghiệp)",
        "desc": "Phiên bản bản quyền doanh nghiệp cho phép chia sẻ nội bộ của Sổ tay Hướng dẫn Quản lý Màu sắc AATCC, phục vụ chuẩn hóa quy trình màu sắc toàn tập đoàn.",
        "scope": "Kiểm soát và đánh giá màu sắc dệt may doanh nghiệp",
        "doc": "AATCC Color Guidebook Corporate",
        "page": "9"
    },
    "08400A": {
        "en": "COLOR VISION & TECHNOLOGY",
        "vi": "Sách Chuyên khảo Sắc giác & Công nghệ Màu sắc",
        "desc": "Tài liệu tham khảo toàn diện về khoa học sắc giác và công nghệ đo màu của tác giả Rolf Kuehni dạng PDF có thể tra cứu và tìm kiếm nhanh thuật ngữ chuyên ngành.",
        "scope": "Khoa học màu sắc và đo màu quang phổ",
        "doc": "Tài liệu Công nghệ Đo màu AATCC",
        "page": "9"
    },
    "08606A": {
        "en": "COLOR: FROM CONCEPT TO CONSUMER (PDF Download)",
        "vi": "Sách Màu sắc Dệt may: Từ Ý tưởng đến Người tiêu dùng",
        "desc": "Tài liệu phân tích chuyên sâu các kịch bản thực tế về nhuộm đúng màu trong sản xuất dệt may của GS. Martin Bide (xuất bản năm 2024), phục vụ kỹ sư nhuộm và QA/QC.",
        "scope": "Kỹ thuật nhuộm và kiểm soát chất lượng màu dệt may",
        "doc": "AATCC Color Concept to Consumer",
        "page": "9"
    },

    # Page 10
    "08506A": {
        "en": "ANALYTICAL METHODS FOR A TEXTILE LABORATORY (4th Edition)",
        "vi": "Sổ tay Phương pháp Phân tích Phòng Thí nghiệm Dệt may (Tái bản lần 4)",
        "desc": "Cẩm nang các phương pháp phân tích chung trong phòng lab dệt may: phân tích đơn xơ, mặt cắt xơ, phân tích hư hại sợi, định danh nhóm thuốc nhuộm, formaldehyde, quang phổ hồng ngoại FTIR, sắc ký...",
        "scope": "Phân tích hóa lý và kiểm nghiệm xơ sợi dệt may",
        "doc": "AATCC Analytical Methods for Textile Laboratory",
        "page": "10"
    },
    "09907A": {
        "en": "SELECTING A TEXTILE TESTING LAB (PDF Download)",
        "vi": "Hướng dẫn Lựa chọn Phòng Thử nghiệm Dệt may (Bản điện tử PDF)",
        "desc": "Cẩm nang hướng dẫn đánh giá và lựa chọn phòng lab kiểm nghiệm dệt may đạt chuẩn năng lực, chứng nhận quốc tế và phát triển phương pháp thử của Diana Wyman.",
        "scope": "Quản lý chất lượng và năng lực phòng lab thử nghiệm",
        "doc": "AATCC Selecting a Textile Testing Lab",
        "page": "10"
    },
    "09907B": {
        "en": "SELECTING A TEXTILE TESTING LAB (Paperback)",
        "vi": "Hướng dẫn Lựa chọn Phòng Thử nghiệm Dệt may (Sách in bìa mềm)",
        "desc": "Phiên bản sách in bìa mềm hướng dẫn lựa chọn phòng thử nghiệm dệt may đạt chuẩn quốc tế, tiêu chí đánh giá dịch vụ chuyên sâu và năng lực QA/QC.",
        "scope": "Quản lý chất lượng và năng lực phòng lab thử nghiệm",
        "doc": "AATCC Selecting a Textile Testing Lab",
        "page": "10"
    },
    "09506A": {
        "en": "GARMENT WET PROCESSING TECHNICAL MANUAL",
        "vi": "Sổ tay Kỹ thuật Xử lý Ướt May mặc (Garment Wet Processing)",
        "desc": "Tài liệu kỹ thuật toàn diện về quy trình giặt, nhuộm, wash và hoàn tất ướt cho sản phẩm may mặc thành phẩm trong ngành công nghiệp thời trang.",
        "scope": "Quy trình xử lý ướt và wash may mặc",
        "doc": "AATCC Garment Wet Processing Manual",
        "page": "10"
    },
    "08336A": {
        "en": "DYEING PRIMER (Hardbound)",
        "vi": "Sách Nhập môn Kỹ thuật Nhuộm Dệt may (Dyeing Primer - Bìa cứng)",
        "desc": "Tuyển tập các bài viết nền tảng chuyên sâu về kỹ thuật nhuộm cho từng loại xơ sợi, thuốc nhuộm và quy trình chuẩn bị vải trước khi nhuộm.",
        "scope": "Kỹ thuật nhuộm và chuẩn bị vải dệt may",
        "doc": "AATCC Dyeing Primer",
        "page": "10"
    },

    # Page 14 - Detergents
    "48349F": {
        "en": "AATCC 1993 STANDARD REFERENCE DETERGENT WOB (75 kg Drum)",
        "vi": "Chất tẩy chuẩn AATCC 1993 không chất tăng trắng WOB (Phuy 75 kg)",
        "desc": "Bột giặt chuẩn đối chứng AATCC 1993 dạng bột không chứa chất tăng trắng quang học (WOB), chuyên dùng thử nghiệm độ bền màu khi giặt gia đình. Đạt chuẩn OEKO-TEX ECO PASSPORT và ZDHC Cấp 1.",
        "scope": "Tiêu chuẩn giặt gia đình và độ bền màu AATCC",
        "doc": "Tiêu chuẩn phương pháp giặt AATCC TM61 / TM135",
        "page": "14"
    },
    "49145F": {
        "en": "AATCC 1993 STANDARD REFERENCE DETERGENT WITH BRIGHTENER (75 kg Drum)",
        "vi": "Chất tẩy chuẩn AATCC 1993 có chất tăng trắng quang học (Phuy 75 kg)",
        "desc": "Bột giặt chuẩn đối chứng AATCC 1993 dạng bột có chứa chất tăng trắng quang học (With Brightener) phục vụ thử nghiệm giặt gia đình theo tiêu chuẩn quốc tế. Đạt chứng nhận OEKO-TEX và ZDHC.",
        "scope": "Tiêu chuẩn giặt gia đình và độ bền màu AATCC",
        "doc": "Tiêu chuẩn phương pháp giặt AATCC TM61 / TM135",
        "page": "14"
    },
    "48349E": {
        "en": "AATCC 1993 STANDARD REFERENCE DETERGENT WOB (7.3 kg Bucket)",
        "vi": "Chất tẩy chuẩn AATCC 1993 không chất tăng trắng WOB (Thùng 7.3 kg)",
        "desc": "Chất tẩy chuẩn đối chứng AATCC 1993 không chất tăng trắng quang học (WOB) quy cách thùng 7.3 kg, phù hợp các phòng lab thử nghiệm độ bền màu với giặt và độ co giãn vải.",
        "scope": "Tiêu chuẩn giặt gia đình và độ bền màu AATCC",
        "doc": "Tiêu chuẩn phương pháp giặt AATCC TM61 / TM135",
        "page": "14"
    },
    "49145E": {
        "en": "AATCC 1993 STANDARD REFERENCE DETERGENT WITH BRIGHTENER (7.3 kg Bucket)",
        "vi": "Chất tẩy chuẩn AATCC 1993 có chất tăng trắng quang học (Thùng 7.3 kg)",
        "desc": "Bột giặt chuẩn đối chứng AATCC 1993 có chất tăng trắng quang học quy cách thùng 7.3 kg, chuyên dùng cho các phép thử giặt gia đình AATCC TM61, TM135, TM150.",
        "scope": "Tiêu chuẩn giặt gia đình và độ bền màu AATCC",
        "doc": "Tiêu chuẩn phương pháp giặt AATCC TM61 / TM135",
        "page": "14"
    },
    "48805B": {
        "en": "AATCC HE STANDARD REFERENCE LIQUID DETERGENT (11.5 L Bucket)",
        "vi": "Chất tẩy lỏng chuẩn AATCC HE không chất tăng trắng WOB (Thùng 11.5 L)",
        "desc": "Nước giặt chuẩn đối chứng hiệu suất cao (HE Liquid Detergent) không chứa chất tăng trắng quang học (WOB) dùng cho máy giặt cửa trước hiệu suất cao theo phương pháp giặt gia đình AATCC.",
        "scope": "Tiêu chuẩn kiểm nghiệm giặt máy hiệu suất cao HE",
        "doc": "Tiêu chuẩn phương pháp giặt AATCC TM61 / TM135 / TM150",
        "page": "14"
    },
    "48723A": {
        "en": "AATCC DETERGENT 171 (5 lb Container)",
        "vi": "Chất tẩy chuẩn làm sạch thảm AATCC Detergent 171 (Hộp 5 lb)",
        "desc": "Chất tẩy rửa chuẩn AATCC 171 chuyên dụng cho phương pháp thử AATCC TM171 - Làm sạch thảm trải sàn bằng phương pháp chiết xuất nước nóng (Hot Water Extraction).",
        "scope": "Kiểm nghiệm độ bền và làm sạch thảm dệt AATCC TM171",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM171",
        "page": "14"
    },

    # Page 15 - Scales
    "28359C": {
        "en": "AATCC GRAY SCALE FOR COLOR CHANGE",
        "vi": "Thước xám chuẩn đánh giá độ thay đổi màu AATCC (Color Change)",
        "desc": "Thước xám chuẩn 5 cấp độ (9 bước chia) dùng để đánh giá trực quan sự thay đổi màu sắc của mẫu vải sau các phép thử nghiệm độ bền màu theo AATCC EP1 hoặc ISO 105-A02. Khuyến nghị thay mới hàng năm.",
        "scope": "Đánh giá cấp độ biến màu dệt may AATCC EP1 / ISO 105-A02",
        "doc": "Quy trình đánh giá AATCC EP1",
        "page": "15"
    },
    "28360C": {
        "en": "AATCC GRAY SCALE FOR STAINING",
        "vi": "Thước xám chuẩn đánh giá độ dây màu AATCC (Staining)",
        "desc": "Thước xám chuẩn 5 cấp độ dùng để đánh giá trực quan mức độ dây màu lên vải kèm theo sau các thử nghiệm độ bền màu theo AATCC EP2 hoặc ISO 105-A03. Khuyến nghị thay mới hàng năm.",
        "scope": "Đánh giá cấp độ dây màu dệt may AATCC EP2 / ISO 105-A03",
        "doc": "Quy trình đánh giá AATCC EP2",
        "page": "15"
    },
    "28347A": {
        "en": "AATCC 9-STEP CHROMATIC TRANSFERENCE SCALE",
        "vi": "Thước màu chuẩn 9 bước đánh giá độ dây màu AATCC (Chromatic Scale)",
        "desc": "Thước màu chuẩn gồm 9 bước chia màu sắc hiển thị dùng để đánh giá độ dây màu và chuyển dịch màu trong thử nghiệm độ bền ma sát Crockmeter theo AATCC EP8.",
        "scope": "Đánh giá độ dây màu ma sát dệt may AATCC EP8",
        "doc": "Quy trình đánh giá AATCC EP8",
        "page": "15"
    },
    "19129A": {
        "en": "AATCC RED 40 STAIN SCALE",
        "vi": "Thước chuẩn đánh giá độ bám vết bẩn Red 40 trên thảm AATCC",
        "desc": "Thước chuẩn 10 cấp độ màu dùng để đánh giá độ kháng vết bẩn màu đỏ Red 40 trên thảm trải sàn theo tiêu chuẩn phương pháp thử AATCC TM175.",
        "scope": "Kiểm nghiệm độ kháng bẩn thảm sàn AATCC TM175",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM175",
        "page": "15"
    },

    # Page 16 - 3D Replicas
    "68353A": {
        "en": "AATCC 3D SMOOTHNESS APPEARANCE REPLICAS",
        "vi": "Bộ mẫu chuẩn 3D đánh giá độ phẳng bề mặt vải AATCC (Bộ 6 mẫu)",
        "desc": "Bộ mẫu chuẩn 3D gồm 6 mô hình bằng nhựa đúc dùng để đánh giá trực quan độ phẳng bề mặt của vải và sản phẩm may mặc sau khi giặt gia đình nhiều lần theo AATCC TM124.",
        "scope": "Đánh giá độ phẳng ngoại quan vải dệt may AATCC TM124",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM124",
        "page": "16"
    },
    "68373A": {
        "en": "AATCC PHOTOGRAPHIC SEAM SMOOTHNESS SCALES",
        "vi": "Thước ảnh chuẩn đánh giá độ phẳng đường may AATCC (Bộ 2 thước)",
        "desc": "Thước ảnh chuẩn dùng để đánh giá trực quan độ phẳng và độ nhăn của đường may đơn và may đôi trên sản phẩm may mặc sau giặt gia đình theo AATCC TM88B.",
        "scope": "Đánh giá độ phẳng đường may AATCC TM88B",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM88B",
        "page": "16"
    },
    "68720A": {
        "en": "AATCC 3D CREASE REPLICAS",
        "vi": "Bộ mẫu chuẩn 3D đánh giá nếp gấp / nếp ly vải AATCC (Bộ 5 mẫu)",
        "desc": "Bộ mẫu chuẩn 3D gồm 5 mô hình dùng để đánh giá trực quan khả năng duy trì nếp ly, nếp gấp trên quần áo và vải dệt thoi sau giặt theo AATCC TM88C.",
        "scope": "Đánh giá khả năng duy trì nếp ly AATCC TM88C",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM88C",
        "page": "16"
    },
    "68390A": {
        "en": "AATCC 3D WRINKLE RECOVERY REPLICAS",
        "vi": "Bộ mẫu chuẩn 3D đánh giá phục hồi nếp nhăn AATCC (Bộ 5 mẫu)",
        "desc": "Bộ mẫu chuẩn 3D gồm 5 mô hình dùng để đánh giá trực quan khả năng tự phục hồi nếp nhăn của vải sau khi bị ép nén theo phương pháp thử AATCC TM128.",
        "scope": "Đánh giá độ phục hồi nếp nhăn vải dệt AATCC TM128",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM128",
        "page": "16"
    },
    "68379A": {
        "en": "STAIN RELEASE SCALE",
        "vi": "Thước chuẩn đánh giá khả năng giặt sạch vết bẩn dệt may AATCC",
        "desc": "Thước ảnh chuẩn dùng để xếp hạng mức độ sạch của vết bẩn dầu mỡ sau khi giặt theo phương pháp AATCC TM130 - Soil Release: Oily Stain Release Method.",
        "scope": "Đánh giá khả năng tẩy sạch vết bẩn dầu AATCC TM130",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM130",
        "page": "16"
    },

    # Page 17 - Control & Lightfastness
    "78387A": {
        "en": "AATCC PHOTOGRAPHIC SPRAY TEST EVALUATION SCALE",
        "vi": "Bảng ảnh chuẩn đánh giá độ ngấm nước AATCC Spray Test Chart",
        "desc": "Bảng ảnh chuẩn minh họa các mức độ thấm ướt bề mặt từ 0 đến 100 dùng cho phương pháp thử nghiệm độ ngấm nước bề mặt vải dệt AATCC TM22.",
        "scope": "Đánh giá độ kháng thấm nước bề mặt AATCC TM22",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM22",
        "page": "17"
    },
    "58335A": {
        "en": "AATCC PHOTOGRAPHIC FILTER RESIDUE SCALE",
        "vi": "Thước ảnh chuẩn đánh giá cặn lọc thuốc nhuộm phân tán AATCC",
        "desc": "Thước ảnh chuẩn dùng đánh giá mức độ cặn bám trên giấy lọc khi kiểm tra khả năng phân tán của thuốc nhuộm phân tán theo phương pháp AATCC TM146.",
        "scope": "Kiểm nghiệm độ phân tán thuốc nhuộm AATCC TM146",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM146",
        "page": "17"
    },
    "58725A": {
        "en": "AATCC PHOTOGRAPHIC DYE DUSTING SCALE",
        "vi": "Thước ảnh chuẩn đánh giá độ tạo bụi của thuốc nhuộm bột AATCC",
        "desc": "Thước ảnh chuẩn dùng để xếp hạng xu hướng tạo bụi của thuốc nhuộm dạng bột khi thao tác cân đong trong phòng lab và nhà nhuộm theo AATCC TM170.",
        "scope": "Kiểm nghiệm độ tạo bụi thuốc nhuộm AATCC TM170",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM170",
        "page": "17"
    },
    "38362C": {
        "en": "BLUE WOOL LIGHTFASTNESS STANDARD L2 (Specimen Sheet)",
        "vi": "Mẫu len xanh chuẩn kiểm tra độ bền màu với ánh sáng Blue Wool L2",
        "desc": "Vải len chuẩn nhuộm màu xanh cấp độ L2 dùng làm mẫu đối chứng kiểm soát thời lượng phơi sáng trong thử nghiệm độ bền màu với ánh sáng hồ quang Xenon theo AATCC TM16.",
        "scope": "Kiểm soát phơi sáng độ bền màu ánh sáng AATCC TM16",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM16",
        "page": "17"
    },
    "38610C": {
        "en": "STANDARD OF FADE FOR BLUE WOOL L2",
        "vi": "Mẫu chuẩn phai màu đối chứng cho Len xanh Blue Wool L2",
        "desc": "Mẫu vải len đã được làm phai màu chuẩn xác theo tiêu chuẩn, dùng để so sánh trực quan xác định thời điểm kết thúc phơi sáng của mẫu Blue Wool L2 trong phép thử AATCC TM16.",
        "scope": "Kiểm soát độ phai màu ánh sáng AATCC TM16",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM16",
        "page": "17"
    },
    "38611C": {
        "en": "STANDARD OF FADE FOR BLUE WOOL L4",
        "vi": "Mẫu chuẩn phai màu đối chứng cho Len xanh Blue Wool L4",
        "desc": "Mẫu vải len đã làm phai màu chuẩn đối chứng cho Blue Wool L4, xác định chính xác liều lượng phơi bức xạ ánh sáng trong kiểm nghiệm độ bền màu AATCC TM16.",
        "scope": "Kiểm soát độ phai màu ánh sáng AATCC TM16",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM16",
        "page": "17"
    },

    # Page 18
    "38614C": {
        "en": "LIGHTFASTNESS PACKAGE (Fade to 20 AFU)",
        "vi": "Gói vật tư kiểm tra độ bền màu ánh sáng AATCC (Mức 20 AFU)",
        "desc": "Bộ vật tư kiểm soát phơi sáng trọn gói bao gồm vải chuẩn len xanh Blue Wool L4 và mẫu phai màu đối chứng Standard of Fade đạt mức 20 đơn vị phai màu AATCC (AFU).",
        "scope": "Kiểm nghiệm độ bền màu với ánh sáng Xenon AATCC TM16",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM16",
        "page": "18"
    },
    "38615B": {
        "en": "LIGHTFASTNESS PACKAGE (Fade to 5 AFU)",
        "vi": "Gói vật tư kiểm tra độ bền màu ánh sáng AATCC (Mức 5 AFU)",
        "desc": "Bộ vật tư kiểm soát phơi sáng trọn gói bao gồm vải chuẩn len xanh Blue Wool L2 và mẫu đối chứng phai màu Standard of Fade đạt mức 5 AFU cho phép thử độ bền màu ánh sáng nhanh.",
        "scope": "Kiểm nghiệm độ bền màu với ánh sáng Xenon AATCC TM16",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM16",
        "page": "18"
    },
    "38615C": {
        "en": "LIGHTFASTNESS PACKAGE (Fade to 5 AFU)",
        "vi": "Gói vật tư kiểm tra độ bền màu ánh sáng AATCC (Mức 5 AFU)",
        "desc": "Bộ vật tư kiểm soát phơi sáng trọn gói bao gồm vải chuẩn len xanh Blue Wool L2 và mẫu đối chứng phai màu Standard of Fade đạt mức 5 AFU cho phép thử độ bền màu ánh sáng nhanh.",
        "scope": "Kiểm nghiệm độ bền màu với ánh sáng Xenon AATCC TM16",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM16",
        "page": "18"
    },
    "38371A": {
        "en": "NYLON SLEEVE 129 & STANDARD OF FADE",
        "vi": "Ống vải Nylon 129 & Mẫu chuẩn phai màu kiểm tra độ bền với khí đốt Ozone",
        "desc": "Mẫu vải dệt ống sợi nylon chuẩn số 129 kèm mẫu phai màu chuẩn, chuyên dụng kiểm tra độ bền màu đối với khí ozone và khói khí đốt trong khí quyển theo AATCC TM129.",
        "scope": "Kiểm nghiệm độ bền màu với khí Ozone AATCC TM129",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM129",
        "page": "18"
    },
    "38710A": {
        "en": "CHLORINE TEST CONTROL FABRIC 162",
        "vi": "Vải đối chứng kiểm tra độ bền màu với nước hồ bơi Clo AATCC 162",
        "desc": "Vải chuẩn đối chứng chuyên dùng kiểm tra độ bền màu đối với nước có chứa clo (nước hồ bơi nhân tạo) theo phương pháp thử nghiệm AATCC TM162.",
        "scope": "Kiểm nghiệm độ bền màu với clo AATCC TM162",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM162",
        "page": "18"
    },
    "38618A": {
        "en": "LIGHT TRANSMISSION VERIFICATION FABRIC",
        "vi": "Vải chuẩn kiểm tra độ truyền dẫn ánh sáng và chỉ số chống nắng UV AATCC",
        "desc": "Mẫu vải chuẩn đối chứng dùng để hiệu chuẩn và kiểm tra xác nhận tính năng truyền qua của bức xạ tử ngoại UV trên máy quang phổ UV-Vis theo AATCC TM183.",
        "scope": "Kiểm nghiệm khả năng ngăn tia UV và chỉ số UPF AATCC TM183",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM183",
        "page": "18"
    },

    # Page 19
    "28341A": {
        "en": "MAGNETS FOR VIEWING STAND",
        "vi": "Bộ nam châm gá kẹp mẫu cho giá quan sát màu AATCC (Bộ 4 chiếc)",
        "desc": "Bộ nam châm bọc chuyên dụng dùng để cố định chắc chắn mẫu thử và thước xám trên bề mặt nghiêng 45 độ của giá quan sát màu AATCC Viewing Stand.",
        "scope": "Phụ kiện phòng so màu và quan sát ngoại quan",
        "doc": "AATCC Viewing Stand Accessories",
        "page": "19"
    },
    "28342A": {
        "en": "VIEWING STAND",
        "vi": "Giá quan sát và so màu mẫu dệt may góc nghiêng 45 độ AATCC",
        "desc": "Giá đỡ quan sát tiêu chuẩn góc nghiêng 45 độ, bề mặt sơn xám trung tính Munsell N7 chuyên dùng đặt mẫu vải và thước xám trong tủ so màu theo AATCC EP1 và EP2.",
        "scope": "Thiết bị quan sát và đánh giá màu sắc dệt may",
        "doc": "Quy trình đánh giá AATCC EP1 / EP2",
        "page": "19"
    },
    "28510A": {
        "en": "GRAY CARD STOCK (Pack of 50)",
        "vi": "Bìa giấy xám chuẩn đệm nền so màu AATCC (Tập 50 tờ)",
        "desc": "Bìa giấy màu xám trung tính chuẩn chuyên dùng làm tấm đệm nền che chắn phía sau mẫu vải khi đánh giá độ thay đổi màu và dây màu, loại trừ nhiễu nền.",
        "scope": "Vật tư phụ trợ phòng thử nghiệm so màu dệt may",
        "doc": "Quy trình đánh giá màu sắc AATCC",
        "page": "19"
    },

    # Page 20
    "58343A": {
        "en": "BASIC DYES (Set of 10 Bottles)",
        "vi": "Bộ thuốc nhuộm bazo chuẩn kiểm tra độ tương thích xơ Acrylic (Bộ 10 màu)",
        "desc": "Bộ gồm 10 lọ thuốc nhuộm bazo chuẩn (mỗi lọ 50g) chuyên dùng thử nghiệm độ tương thích của thuốc nhuộm bazo đối với xơ sợi acrylic theo AATCC TM141.",
        "scope": "Kiểm nghiệm độ tương thích thuốc nhuộm AATCC TM141",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM141",
        "page": "20"
    },
    "79164A": {
        "en": "FIBER FRAGMENT VACUUM FILTER SET",
        "vi": "Bộ lọc chân không thu gom vi sợi phát thải khi giặt AATCC TM212",
        "desc": "Bộ thiết bị lọc hút chân không thủy tinh 47mm hoàn chỉnh, bao gồm màng lọc sợi thủy tinh, đĩa cân nhôm 57mm, hướng dẫn sử dụng và tiêu chuẩn AATCC TM212.",
        "scope": "Kiểm nghiệm phát thải vi nhựa / vi sợi dệt may AATCC TM212",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM212",
        "page": "20"
    },
    "79165A": {
        "en": "FIBER FRAGMENT FILTERS & DISH KIT",
        "vi": "Bộ màng lọc sợi thủy tinh và đĩa cân nhôm AATCC TM212",
        "desc": "Bộ vật tư tiêu hao gồm các màng lọc sợi thủy tinh đường kính 47mm và đĩa cân nhôm 57mm chuyên dùng cho phép thử nghiệm đo lường phát thải vi sợi AATCC TM212.",
        "scope": "Kiểm nghiệm phát thải vi sợi dệt may AATCC TM212",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM212",
        "page": "20"
    },
    "58380A": {
        "en": "STAINLESS STEEL RING FOR DYE FILTER TEST",
        "vi": "Vòng thép không gỉ gá giữ giấy lọc phân tán thuốc nhuộm AATCC",
        "desc": "Vòng inox tiêu chuẩn dùng để giữ phẳng và cố định giấy lọc trong phép thử kiểm tra khả năng phân tán của thuốc nhuộm theo phương pháp AATCC TM146.",
        "scope": "Thử nghiệm độ phân tán thuốc nhuộm AATCC TM146",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM146",
        "page": "20"
    },
    "58727A": {
        "en": "DYE DUSTING PAPER COLLARS (Pack of 48)",
        "vi": "Vành giấy thu bụi thuốc nhuộm bột AATCC (Hộp 48 chiếc)",
        "desc": "Vành giấy tiêu chuẩn dùng thu giữ các hạt bụi thuốc nhuộm phát tán trong thiết bị đo độ tạo bụi của thuốc nhuộm dạng bột theo phương pháp thử AATCC TM170.",
        "scope": "Đánh giá mức độ phát tán bụi thuốc nhuộm AATCC TM170",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM170",
        "page": "20"
    },

    # Page 21
    "58756A": {
        "en": "STAINLESS STEEL FUNNEL AND CYLINDER",
        "vi": "Bộ phễu và ống đong thép không gỉ đo độ tạo bụi thuốc nhuộm AATCC",
        "desc": "Bộ phễu rót và ống hình trụ bằng inox không gỉ chuyên dụng trong thiết bị đo lường khuynh hướng tạo bụi của thuốc nhuộm theo tiêu chuẩn AATCC TM170.",
        "scope": "Kiểm nghiệm độ tạo bụi thuốc nhuộm AATCC TM170",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM170",
        "page": "21"
    },
    "59127A": {
        "en": "CROSS-SECTION SLIDES",
        "vi": "Lam kính soi mặt cắt ngang xơ sợi vi phẫu AATCC",
        "desc": "Lam kính chuyên dụng soi kính hiển vi dùng gá đặt mẫu mặt cắt ngang của xơ sợi dệt may trong quy trình định tính và phân tích xơ sợi theo AATCC TM20.",
        "scope": "Phân tích vi phẫu cấu trúc xơ sợi AATCC TM20",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM20",
        "page": "21"
    },
    "59130A": {
        "en": "YARN AND FABRIC HOLDERS FOR MICROSCOPIC ANALYSIS",
        "vi": "Bộ đồ gá kẹp sợi và vải phục vụ phân tích kính hiển vi AATCC",
        "desc": "Bộ gá kẹp mẫu sợi và mẫu vải chuyên dụng giúp định vị vững chắc mẫu vật dưới kính hiển vi quang học phục vụ nghiên cứu và phân tích cấu trúc dệt may.",
        "scope": "Phân tích quang học và cấu trúc xơ sợi dệt may",
        "doc": "Tiêu chuẩn phân tích hiển vi AATCC TM20",
        "page": "21"
    },
    "59138A": {
        "en": "MICROSCOPY CROSS-SECTION KIT",
        "vi": "Bộ dụng cụ cắt lát vi phẫu mặt cắt ngang xơ sợi AATCC",
        "desc": "Bộ dụng cụ hoàn chỉnh hỗ trợ tạo lát cắt ngang siêu mỏng của xơ sợi dệt may bao gồm dao cắt chuyên dụng, phụ kiện chêm sợi và hướng dẫn kỹ thuật phòng lab.",
        "scope": "Chuẩn bị mẫu vi phẫu xơ sợi AATCC TM20",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM20",
        "page": "21"
    },
    "59144A": {
        "en": "FILLER YARN FOR CROSS-SECTIONS",
        "vi": "Sợi chêm độn hỗ trợ cắt vi phẫu mặt cắt ngang xơ sợi AATCC",
        "desc": "Cuộn sợi chêm độn chuyên dụng dùng để bó chặt các xơ sợi mẫu trong quá trình cắt lát vi phẫu, đảm bảo mặt cắt phẳng không bị biến dạng cấu trúc xơ.",
        "scope": "Chuẩn bị mẫu phân tích xơ sợi AATCC TM20",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM20",
        "page": "21"
    },

    # Page 22
    "68391A": {
        "en": "WRINKLE TESTER (110V)",
        "vi": "Máy thử nghiệm phục hồi nếp nhăn vải AATCC Wrinkle Tester (110V)",
        "desc": "Thiết bị thử nghiệm độ phục hồi nếp nhăn của vải dệt sau khi chịu tải trọng nén ép quy chuẩn theo phương pháp AATCC TM128. Phiên bản điện áp 110V.",
        "scope": "Kiểm nghiệm độ phục hồi nếp nhăn AATCC TM128",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM128",
        "page": "22"
    },
    "68392A": {
        "en": "WRINKLE TESTER (230V)",
        "vi": "Máy thử nghiệm phục hồi nếp nhăn vải AATCC Wrinkle Tester (230V)",
        "desc": "Thiết bị thử nghiệm độ phục hồi nếp nhăn vải sau nén ép quy chuẩn theo phương pháp AATCC TM128. Phiên bản điện áp 230V phù hợp hệ thống điện Việt Nam.",
        "scope": "Kiểm nghiệm độ phục hồi nếp nhăn AATCC TM128",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM128",
        "page": "22"
    },
    "68393A": {
        "en": "WRINKLE TESTER WEIGHTS",
        "vi": "Bộ quả nặng gia tải máy thử nếp nhăn AATCC Wrinkle Tester",
        "desc": "Bộ quả tải trọng quy chuẩn dùng trên máy thử phục hồi nếp nhăn vải dệt AATCC TM128, đảm bảo lực nén ép chính xác và đồng đều lên mẫu vải.",
        "scope": "Phụ kiện thiết bị thử nếp nhăn AATCC TM128",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM128",
        "page": "22"
    },
    "68357A": {
        "en": "GLASSINE PAPER",
        "vi": "Giấy lót bóng Glassine Paper cho máy thử nếp nhăn AATCC (Tập 500 tờ)",
        "desc": "Giấy lót phẳng bề mặt glassine chuyên dụng dùng để lót bao quanh mẫu vải khi lắp vào máy thử nếp nhăn AATCC TM128 nhằm tránh ma sát cọ xát cơ học.",
        "scope": "Vật tư tiêu hao thử nếp nhăn AATCC TM128",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM128",
        "page": "22"
    },
    "68381A": {
        "en": "5 LB CYLINDER WEIGHT",
        "vi": "Quả tải trọng hình trụ 5 lb cho máy thử nếp nhăn AATCC",
        "desc": "Quả tải hình trụ khối lượng chuẩn 5 lb (2.27 kg) chế tạo chính xác theo thông số phương pháp thử nghiệm phục hồi nếp nhăn vải dệt AATCC TM128.",
        "scope": "Vật tư gia tải thử nếp nhăn AATCC TM128",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM128",
        "page": "22"
    },
    "68377A": {
        "en": "SHRINKAGE & SKEW TEMPLATE",
        "vi": "Thước mẫu đo độ co ngót và độ xoắn vải dệt may AATCC Template",
        "desc": "Thước dưỡng định hình bằng nhựa acrylic trong suốt có khắc vạch đo tỷ lệ phần trăm co giãn kích thước và độ lệch canh sợi (độ xoắn) vải theo AATCC TM135, TM150, TM179.",
        "scope": "Đo độ co giãn và độ xiên lệch canh sợi AATCC TM135 / TM179",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM135 / TM179",
        "page": "22"
    },

    # Page 23
    "68375A": {
        "en": "SHRINKAGE SCALE",
        "vi": "Thước đo tỷ lệ phần trăm co giãn dệt may AATCC Shrinkage Scale",
        "desc": "Thước đo vạch chia chuẩn đọc trực tiếp tỷ lệ co giãn kích thước (phần trăm) của vải và hàng may mặc sau các chu kỳ giặt theo AATCC TM135 và TM150.",
        "scope": "Đo lường độ co giãn kích thước vải AATCC TM135",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM135",
        "page": "23"
    },

    # Page 24 - Water Testing
    "78733A": {
        "en": "IMPACT PENETRATION TESTER (Type I)",
        "vi": "Thiết bị thử nghiệm độ thấm nước va đập AATCC Impact Penetration (Loại 1)",
        "desc": "Thiết bị đo khả năng chống thấm nước của vải khi chịu tia nước va đập áp lực rơi tự do theo phương pháp thử AATCC TM42. Cấu hình tiêu chuẩn Type I.",
        "scope": "Kiểm nghiệm độ kháng nước vải áo mưa và y tế AATCC TM42",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM42",
        "page": "24"
    },
    "78734A": {
        "en": "IMPACT PENETRATION TESTER (Type II)",
        "vi": "Thiết bị thử nghiệm độ thấm nước va đập AATCC Impact Penetration (Loại 2)",
        "desc": "Thiết bị thử nghiệm chống thấm nước va đập AATCC TM42 cấu hình Loại 2 chuyên dụng kiểm tra vải trang phục bảo hộ y tế, vải phòng dịch theo tiêu chuẩn quốc tế.",
        "scope": "Kiểm nghiệm độ kháng nước vải bảo hộ y tế AATCC TM42",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM42",
        "page": "24"
    },
    "78384A": {
        "en": "IMPACT PENETRATION TESTER NOZZLE",
        "vi": "Đầu phun tạo tia nước thiết bị thử thấm va đập AATCC TM42",
        "desc": "Đầu vòi phun gia công chính xác bằng đồng/inox quy chuẩn theo tiêu chuẩn AATCC TM42, đảm bảo phân bố dòng nước va đập đồng nhất và đúng áp lực.",
        "scope": "Phụ kiện thiết bị thử thấm nước AATCC TM42",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM42",
        "page": "24"
    },
    "78383A": {
        "en": "IMPACT PENETRATION CLIP & PLATE",
        "vi": "Kẹp gá và tấm kẹp mẫu thiết bị thử thấm va đập AATCC TM42",
        "desc": "Bộ kẹp mẫu và tấm kim loại đỡ góc nghiêng tiêu chuẩn giữ cố định mẫu vải và giấy thấm đệm phía sau trong phép thử thấm nước AATCC TM42.",
        "scope": "Phụ kiện thiết bị thử thấm nước AATCC TM42",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM42",
        "page": "24"
    },
    "78382A": {
        "en": "IMPACT PENETRATION FUNNEL ASSEMBLY",
        "vi": "Cụm phễu rót nước thiết bị thử thấm va đập AATCC TM42",
        "desc": "Cụm phễu và ống dẫn nước rơi quy chuẩn gắn trên giá đỡ định vị chiều cao chính xác của thiết bị thử thấm va đập AATCC TM42.",
        "scope": "Phụ kiện thiết bị thử thấm nước AATCC TM42",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM42",
        "page": "24"
    },
    "78385A": {
        "en": "SPRAY TESTER COMPLETE",
        "vi": "Thiết bị thử nghiệm độ ngấm nước phun sương AATCC Spray Tester hoàn chỉnh",
        "desc": "Thiết bị kiểm tra độ ngấm nước bề mặt vải hoàn chỉnh bao gồm phễu rót, đầu vòi sen phun, vòng căng mẫu nghiêng 45 độ và giá đỡ theo phương pháp AATCC TM22.",
        "scope": "Kiểm nghiệm độ chống ngấm nước bề mặt vải AATCC TM22",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM22",
        "page": "24"
    },
    "78911A": {
        "en": "SPRAY TESTER FUNNEL",
        "vi": "Phễu chứa nước thủy tinh thiết bị thử phun sương AATCC TM22",
        "desc": "Phễu rót nước quy chuẩn chế tạo theo thông số kỹ thuật tiêu chuẩn thử nghiệm độ chống ngấm nước AATCC TM22.",
        "scope": "Phụ kiện thiết bị thử Spray Tester AATCC TM22",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM22",
        "page": "24"
    },
    "78388A": {
        "en": "SPRAY TESTER HOOP",
        "vi": "Vòng căng kẹp mẫu thử phun sương AATCC TM22",
        "desc": "Vòng khung kẹp căng mẫu vải giữ bề mặt vải luôn phẳng và căng đều ở góc nghiêng 45 độ dưới vòi phun nước của thiết bị AATCC TM22.",
        "scope": "Phụ kiện thiết bị thử Spray Tester AATCC TM22",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM22",
        "page": "24"
    },
    "78386A": {
        "en": "SPRAY TESTER NOZZLE",
        "vi": "Đầu vòi sen phun nước thiết bị thử phun sương AATCC TM22",
        "desc": "Đầu vòi phun dạng hoa sen có các lỗ kim phân bố chính xác tạo hạt nước phun đều lên bề mặt vải thử theo đúng yêu cầu AATCC TM22.",
        "scope": "Phụ kiện thiết bị thử Spray Tester AATCC TM22",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM22",
        "page": "24"
    },

    # Page 25 - Rain Tester & Blotting Paper
    "78728A": {
        "en": "RAIN TESTER COMPLETE (110V)",
        "vi": "Máy thử nghiệm độ chống thấm mưa AATCC Rain Tester hoàn chỉnh (110V)",
        "desc": "Thiết bị đo lường khả năng chống thấm nước của vải dưới tác động của mưa nhân tạo ngang theo phương pháp thử AATCC TM35. Cột nước cao áp, nguồn 110V.",
        "scope": "Kiểm nghiệm độ chống thấm mưa bão dệt may AATCC TM35",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM35",
        "page": "25"
    },
    "78731A": {
        "en": "RAIN TESTER COMPLETE (230V)",
        "vi": "Máy thử nghiệm độ chống thấm mưa AATCC Rain Tester hoàn chỉnh (230V)",
        "desc": "Thiết bị đo lường khả năng chống thấm nước mưa nhân tạo dệt may theo AATCC TM35. Phiên bản điện áp 230V tương thích hoàn toàn hệ thống điện Việt Nam.",
        "scope": "Kiểm nghiệm độ chống thấm mưa bão dệt may AATCC TM35",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM35",
        "page": "25"
    },
    "78729A": {
        "en": "RAIN TESTER COLUMN (110V)",
        "vi": "Cột tạo áp lực nước máy thử mưa AATCC Rain Tester (110V)",
        "desc": "Cột đo thủy tĩnh tạo cột áp lực nước quy chuẩn cho hệ thống máy thử chống thấm nước mưa AATCC TM35 nguồn 110V.",
        "scope": "Phụ kiện máy thử chống thấm mưa AATCC TM35",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM35",
        "page": "25"
    },
    "78730A": {
        "en": "RAIN TESTER COLUMN (230V)",
        "vi": "Cột tạo áp lực nước máy thử mưa AATCC Rain Tester (230V)",
        "desc": "Cột áp lực nước tiêu chuẩn cho máy thử chống mưa AATCC TM35 nguồn 230V, hỗ trợ kiểm soát lưu lượng và áp lực cột nước chính xác.",
        "scope": "Phụ kiện máy thử chống thấm mưa AATCC TM35",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM35",
        "page": "25"
    },
    "78344A": {
        "en": "AATCC BLOTTING PAPER (508 x 1016 mm / 20 x 40 in)",
        "vi": "Giấy thấm thử nghiệm dệt may AATCC Blotting Paper (Khổ 508 x 1016 mm)",
        "desc": "Giấy thấm nước đối chứng đạt chuẩn độ hút nước và độ dày quy định trong các phép thử AATCC TM35, TM42, TM70. Quy cách nguyên tấm khổ lớn 508 x 1016 mm (thùng ~126 tờ).",
        "scope": "Vật tư tiêu hao thử nghiệm chống thấm nước AATCC",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM35 / TM42",
        "page": "25"
    },
    "78344B": {
        "en": "AATCC BLOTTING PAPER (254 x 254 mm / 10 x 10 in)",
        "vi": "Giấy thấm thử nghiệm dệt may AATCC Blotting Paper (Khổ 254 x 254 mm)",
        "desc": "Giấy thấm chuẩn AATCC cắt sẵn kích thước vuông 254 x 254 mm (thùng ~1009 tờ) chuyên dùng cho máy thử chống thấm mưa Rain Tester AATCC TM35.",
        "scope": "Vật tư tiêu hao thử nghiệm chống thấm nước AATCC",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM35",
        "page": "25"
    },
    "78344C": {
        "en": "AATCC BLOTTING PAPER (152 x 230 mm / 6 x 9 in)",
        "vi": "Giấy thấm thử nghiệm dệt may AATCC Blotting Paper (Khổ 152 x 230 mm)",
        "desc": "Giấy thấm chuẩn AATCC cắt sẵn khổ 152 x 230 mm (thùng ~1832 tờ) chuyên dùng làm lớp đệm thấm hút trong thiết bị thử va đập nước AATCC TM42.",
        "scope": "Vật tư tiêu hao thử nghiệm thấm va đập AATCC TM42",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM42",
        "page": "25"
    },
    "78344D": {
        "en": "AATCC BLOTTING PAPER (152 x 152 mm / 6 x 6 in)",
        "vi": "Giấy thấm thử nghiệm dệt may AATCC Blotting Paper (Khổ 152 x 152 mm)",
        "desc": "Giấy thấm chuẩn AATCC cắt sẵn khổ vuông 152 x 152 mm (thùng ~2170 tờ) phục vụ các thử nghiệm độ hút nước và giải phóng vết bẩn dệt may.",
        "scope": "Vật tư tiêu hao phòng kiểm nghiệm dệt may AATCC",
        "doc": "Tiêu chuẩn thử nghiệm độ thấm dệt may AATCC",
        "page": "25"
    },
    "78345A": {
        "en": "AATCC PPE GRADE BLOTTING PAPER",
        "vi": "Giấy thấm chuẩn kiểm nghiệm trang phục bảo hộ PPE Grade AATCC",
        "desc": "Giấy thấm không dệt chuyên dụng cấp độ kiểm nghiệm trang phục bảo hộ y tế (PPE), đáp ứng tiêu chuẩn phân loại AAMI PB70 và quy trình thử nghiệm NWSP 80.3.",
        "scope": "Kiểm nghiệm trang phục bảo hộ y tế AAMI PB70",
        "doc": "Tiêu chuẩn kiểm nghiệm bảo hộ AAMI PB70 / NWSP 80.3",
        "page": "25"
    },
    "79149A": {
        "en": "AATCC VAPOR TRANSMISSION CONTROL PAPER",
        "vi": "Giấy kiểm soát truyền dẫn hơi nước AATCC TM204 (Tập 100 mẫu)",
        "desc": "Giấy đối chứng chuẩn chuyên dùng trong phương pháp thử nghiệm AATCC TM204 - Đo lường độ truyền dẫn hơi nước qua vật liệu dệt may. Đóng gói 100 mẫu cắt sẵn.",
        "scope": "Kiểm nghiệm độ thoát ẩm và truyền dẫn hơi nước AATCC TM204",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM204",
        "page": "25"
    },

    # Page 26 - Sandals & Static
    "19141A": {
        "en": "TM134 SANDALS (Large)",
        "vi": "Dép thử nghiệm tĩnh điện thảm sàn AATCC TM134 (Cỡ Lớn - Large)",
        "desc": "Dép thử nghiệm quy chuẩn cỡ lớn dùng trong phương pháp thử AATCC TM134 - Đo xu hướng tích điện tĩnh điện trên thảm trải sàn khi bước đi.",
        "scope": "Kiểm nghiệm độ tích điện tĩnh điện thảm AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "19141B": {
        "en": "TM134 SANDALS (Small)",
        "vi": "Dép thử nghiệm tĩnh điện thảm sàn AATCC TM134 (Cỡ Nhỏ - Small)",
        "desc": "Dép thử nghiệm quy chuẩn cỡ nhỏ dùng trong phép thử đo điện áp tĩnh điện phát sinh khi đi bộ trên thảm trải sàn theo tiêu chuẩn AATCC TM134.",
        "scope": "Kiểm nghiệm độ tích điện tĩnh điện thảm AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "18378A": {
        "en": "NEOLITE SHEET FOR TM134 (46 x 46 cm)",
        "vi": "Tấm đế cao su Neolite Sheet thử tĩnh điện thảm AATCC TM134 (46 x 46 cm)",
        "desc": "Tấm vật liệu cao su chuẩn Neolite kích thước 46 x 46 cm dùng để gia công cắt đế dép thay thế cho phép thử nghiệm tĩnh điện thảm sàn AATCC TM134.",
        "scope": "Vật liệu đế chuẩn thử tĩnh điện AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "19147A": {
        "en": "SUEDE SOLES FOR TM134 (Large)",
        "vi": "Bộ đế da lộn Suede Soles thử tĩnh điện thảm AATCC TM134 (Cỡ Lớn)",
        "desc": "Bộ đế da lộn chuẩn cỡ lớn dán vào đế dép thử nghiệm bước đi để đo điện áp tĩnh điện phát sinh theo phương pháp thử AATCC TM134.",
        "scope": "Phụ kiện đế chuẩn thử tĩnh điện AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "19147B": {
        "en": "SUEDE SOLES FOR TM134 (Small)",
        "vi": "Bộ đế da lộn Suede Soles thử tĩnh điện thảm AATCC TM134 (Cỡ Nhỏ)",
        "desc": "Bộ đế da lộn chuẩn cỡ nhỏ gắn vào dép thử nghiệm AATCC TM134 để đánh giá xu hướng tích điện của các loại thảm lót sàn dệt may.",
        "scope": "Phụ kiện đế chuẩn thử tĩnh điện AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "19137A": {
        "en": "STANDARD CARPETS FOR STATIC TESTING",
        "vi": "Bộ thảm chuẩn thử nghiệm tĩnh điện AATCC TM134 (Bộ 2 tấm 100 x 100 cm)",
        "desc": "Bộ gồm 2 tấm thảm kích thước 100 x 100 cm (một tấm được xử lý chống tĩnh điện và một tấm không xử lý) dùng đối chứng trong phép thử AATCC TM134.",
        "scope": "Mẫu thảm đối chứng thử tĩnh điện AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "19136A": {
        "en": "STANDARD RUBBERIZED JUTE CUSHION FOR STATIC TESTING",
        "vi": "Tấm đệm lót thảm cao su đay chuẩn thử tĩnh điện AATCC TM134 (100 x 100 cm)",
        "desc": "Tấm đệm lót dưới thảm bằng vật liệu đay tráng cao su quy chuẩn kích thước 100 x 100 cm dùng làm lớp đệm đàn hồi trong phép thử tĩnh điện AATCC TM134.",
        "scope": "Đệm lót chuẩn thử nghiệm tĩnh điện AATCC TM134",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM134",
        "page": "26"
    },
    "18382A": {
        "en": "AATCC STANDARD VINYL TILES",
        "vi": "Gạch lát sàn nhựa Vinyl chuẩn thử nghiệm dệt may AATCC TM137",
        "desc": "Tấm gạch vinyl tiêu chuẩn dùng để kiểm tra sự dây màu và ố màu của lớp đế thảm lên mặt sàn gạch nhựa vinyl theo phương pháp thử AATCC TM137.",
        "scope": "Kiểm nghiệm độ ố dây màu đế thảm AATCC TM137",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM137",
        "page": "26"
    },

    # Page 27
    "19131A": {
        "en": "CARPET-STAIN CUP AND RING SETS",
        "vi": "Bộ cốc và vòng thử nghiệm vết bẩn thảm trải sàn AATCC TM175",
        "desc": "Bộ dụng cụ gồm 2 cốc và 2 vòng định vị chuẩn bằng vật liệu chống bám dính dùng để tạo vết bẩn dung dịch Red 40 lên mẫu thảm sàn theo phương pháp AATCC TM175.",
        "scope": "Thử nghiệm độ kháng bẩn thảm sàn AATCC TM175",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM175",
        "page": "27"
    },
    "19140A": {
        "en": "RED 40 DYE FOR CARPET STAIN TESTING",
        "vi": "Thuốc nhuộm đỏ Red 40 Dye chuẩn thử nghiệm bám bẩn thảm AATCC TM175",
        "desc": "Chất thử màu đỏ Red 40 tinh khiết chuẩn đối chứng chuyên dùng pha dung dịch tạo vết ố để đánh giá độ kháng bám bẩn của sợi thảm theo AATCC TM175.",
        "scope": "Hóa chất đối chứng thử bám bẩn thảm AATCC TM175",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM175",
        "page": "27"
    },
    "88616B": {
        "en": "CONDITIONING / DRYING RACK DRAWINGS (Download Only)",
        "vi": "Bản vẽ kỹ thuật giá điều hòa và phơi khô mẫu dệt may AATCC",
        "desc": "Bản vẽ thiết kế và kích thước kỹ thuật chuẩn của giá phơi và điều hòa mẫu dệt may trong môi trường khí quyển chuẩn phòng lab theo quy định AATCC. Dạng tải về.",
        "scope": "Thiết kế phòng lab điều hòa mẫu dệt may chuẩn AATCC",
        "doc": "Bản vẽ kỹ thuật phòng lab dệt may AATCC",
        "page": "27"
    },
    "88354A": {
        "en": "FABRIC-TO-METAL TEST APPARATUS",
        "vi": "Thiết bị đo độ bám dính tĩnh điện vải với kim loại AATCC TM115",
        "desc": "Thiết bị kiểm nghiệm lực hút và mức độ bám dính tĩnh điện của vải dệt may lên bề mặt kim loại theo phương pháp thử nghiệm AATCC TM115.",
        "scope": "Kiểm nghiệm độ bám dính tĩnh điện AATCC TM115",
        "doc": "Tiêu chuẩn phương pháp thử AATCC TM115",
        "page": "27"
    },
    "88900A": {
        "en": "FARNSWORTH MUNSELL 100-HUE TEST",
        "vi": "Bộ thử sắc giác chuyên sâu Farnsworth Munsell 100-Hue Test",
        "desc": "Hệ thống kiểm tra sắc giác tiêu chuẩn công nghiệp gồm 4 khay chứa 85 nắp mẫu màu chuẩn chuyển sắc liên tục quang phổ, dùng đánh giá độ nhạy và phân loại khiếm khuyết thị giác màu sắc của kỹ thuật viên so màu.",
        "scope": "Đánh giá thị giác màu sắc và năng lực chuyên gia so màu QA/QC",
        "doc": "Tiêu chuẩn kiểm tra sắc giác quốc tế Farnsworth Munsell",
        "page": "27"
    },

    # Page 28
    "88905A": {
        "en": "PSEUDOISOCHROMATIC PLATES (COLOR VISION TEST - 4th Edition)",
        "vi": "Bộ bảng màu kiểm tra mù màu HRR Pseudoisochromatic Plates (Tái bản 4)",
        "desc": "Bộ bảng màu chuẩn HRR (Hardy Rand and Rittler) Standard Pseudoisochromatic Test ấn bản thứ 4 chuyên dùng sàng lọc và chẩn đoán nhanh các dạng khiếm khuyết thị giác màu sắc độc lập với ngôn ngữ.",
        "scope": "Sàng lọc sắc giác và thị giác màu sắc QA/QC phòng lab",
        "doc": "Tiêu chuẩn kiểm tra sắc giác HRR Standard 4th Edition",
        "page": "28"
    }
}


# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, bảo hành, quy định người bán/người mua và đăng bán sản phẩm trên sàn thương mại điện tử (K4-L3B E-Commerce Policies).

**Tại sao nhóm chọn chủ đề này?**
> Bộ dữ liệu chính sách TMĐT chứa nhiều mốc thời gian (3 ngày, 7 ngày, 30 ngày, 48 giờ), hạn mức tài chính (50.000đ, 200.000đ) và đặc biệt phân định rõ ràng giữa các đối tượng tác động (`buyer`, `seller`, `both`). Chủ đề này phản ánh đúng bài toán thực tế của trợ lý hỗ trợ khách hàng và nhà bán hàng, giúp kiểm thử rõ nét hiệu quả của việc lọc metadata (`metadata_filter`).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách đổi trả sản phẩm dành cho Người mua | https://hotro.tiki.vn/s/article/chinh-sach-doi-tra-san-pham-tai-tiki | 2026-09-20 / 2024-v2 | 1,276 | `audience: buyer`, `category: returns-policy`, `language: vi` |
| 2 | Chính sách bảo hành sản phẩm dành cho Người mua | https://hotro.tiki.vn/s/article/chinh-sach-bao-hanh-san-pham-tai-tiki | 2026-09-20 / 2024-v1 | 1,082 | `audience: buyer`, `category: warranty-policy`, `language: vi` |
| 3 | Quy định xử lý đơn hàng và hoàn tiền dành cho Nhà bán hàng | https://hotro.tiki.vn/s/article/quy-trinh-xuy-ly-don-hang-cua-nha-ban | 2026-09-20 / 2024-v3 | 1,053 | `audience: seller`, `category: seller-policy`, `language: vi` |
| 4 | Quy định trách nhiệm bảo hành và chế tài Nhà bán hàng | https://hotro.tiki.vn/s/article/quy-dinh-dang-ban-danh-cho-nha-ban-hang | 2026-09-20 / not-stated | 882 | `audience: seller`, `category: seller-policy`, `language: vi` |
| 5 | Danh mục hàng hóa cấm kinh doanh và quy định đăng bán | https://hotro.tiki.vn/s/article/dieu-khoan-su-dung-dich-vu-tiki | 2026-09-20 / 2024-v1 | 1,073 | `audience: both`, `category: product-policy`, `language: vi` |
| 6 | Quy trình giải quyết tranh chấp và khiếu nại sàn TMĐT | https://hotro.tiki.vn/s/article/chinh-sach-bao-mat-thong-tin | 2026-09-20 / not-stated | 1,092 | `audience: both`, `category: dispute-policy`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | String | `tiki-return-policy-buyer` | Định danh duy nhất cho văn bản, giúp truy xuất chính xác tài liệu nguồn và liên kết `sources.csv`. |
| `audience` | String | `buyer`, `seller`, `both` | Lọc chính xác phạm vi đối tượng áp dụng quy định, tránh trả nhầm chính sách nhà bán cho người mua. |
| `category` | String | `returns-policy`, `seller-policy` | Phân loại mảng nghiệp vụ (đổi trả, bảo hành, hàng cấm), giúp khoanh vùng truy xuất khi câu hỏi nêu rõ danh mục. |
| `document_version` | String | `2024-v2`, `not-stated` | Xác định phiên bản quy định hiệu lực, ngăn chặn việc lấy tài liệu cũ lỗi thời. |
| `source_url` | String | `https://hotro.tiki.vn/...` | Cung cấp đường dẫn trích dẫn minh bạch cho người dùng kiểm chứng thông tin. |
| `language` | String | `vi` | Phân loại ngôn ngữ của văn bản phục vụ xử lý đa ngôn ngữ nếu có. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |

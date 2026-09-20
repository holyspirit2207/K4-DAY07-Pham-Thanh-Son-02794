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

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên bộ tài liệu chính sách TMĐT (`chunk_size=400`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Bộ dữ liệu TMĐT 6 file | FixedSizeChunker (`fixed_size`) | 19 | 388.7 | Trung bình — dễ cắt đôi giữa câu hoặc giữa điều khoản. |
| Bộ dữ liệu TMĐT 6 file | SentenceChunker (`by_sentences`) | 20 | 321.6 | Tốt cho câu đơn, nhưng làm rời rạc các điều khoản nhiều câu. |
| Bộ dữ liệu TMĐT 6 file | RecursiveChunker (`recursive`) | 23 | 279.8 | Rất tốt — ưu tiên cắt theo ranh giới đoạn văn và câu tự nhiên. |

### Chiến lược của từng thành viên

**Thành viên 1 — Phạm Thanh Sơn (Data Lead)**
- **Loại chiến lược:** Custom `HeadingChunker` (`max_chunk_size=500`)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản chính sách Thương mại Điện tử được cấu trúc rất rõ ràng theo các tiêu đề mục (`#`, `##`, `###`). Việc chia nhỏ theo heading giúp giữ nguyên vẹn toàn bộ 1 điều khoản (như mốc thời gian 7-30 ngày hoặc quy trình hoàn tiền) trong một chunk duy nhất, tránh việc ngữ cảnh bị cắt vụn.
- **Code snippet (nếu custom):**
```python
class HeadingChunker:
    """Custom Chunker cho chính sách TMĐT: Chia theo tiêu đề Markdown (#, ##, ###)."""
    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sections = re.split(r'(?=\n#{1,3}\s+)', text.strip())
        chunks: list[str] = []
        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            if len(sec_clean) <= self.max_chunk_size:
                chunks.append(sec_clean)
            else:
                sub_chunker = RecursiveChunker(chunk_size=self.max_chunk_size)
                chunks.extend(sub_chunker.chunk(sec_clean))
        return chunks
```

**Thành viên 2 — Đào Minh Hiếu (Benchmark Lead)**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=400`)
- **Mô tả & lý do chọn:** Đệ quy cắt theo ranh giới ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Chiến lược này cân bằng tuyệt vời giữa độ dài chunk và việc giữ nguyên cấu trúc đoạn văn bản.

**Thành viên 3 — Thành viên 3 (Strategy Lead)**
- **Loại chiến lược:** `FixedSizeChunker` (`chunk_size=500`, `overlap=50`)
- **Mô tả & lý do chọn:** Chia cố định 500 ký tự với 50 ký tự gối đầu (overlap). Đảm bảo kích thước đồng đều và không bị đứt đoạn thông tin giữa các ranh giới chunk.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phạm Thanh Sơn | Custom `HeadingChunker` | 10 / 10 | Giữ trọn vẹn ngữ cảnh tiêu đề và điều khoản chính sách TMĐT. | Cần văn bản có cấu trúc Markdown chuẩn (`#`, `##`). |
| Đào Minh Hiếu | `RecursiveChunker` | 9.5 / 10 | Linh hoạt, tự động hạ cấp separator khi đoạn quá dài. | Kích thước chunk không đồng đều giữa các điều khoản. |
| Thành viên 3 | `FixedSizeChunker` | 8.5 / 10 | Dễ cài đặt, kích thước chunk đồng nhất. | Thỉnh thoảng bị cắt giữa câu hoặc giữa bảng thông số. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Đăng ký và phân tích quy định TMĐT tốt nhất khi dùng **`HeadingChunker` kết hợp `RecursiveChunker`**. Lý do vì văn bản pháp lý / chính sách TMĐT có tính cấu trúc mục rất cao; giữ trọn vẹn tiêu đề điều khoản kèm theo các mốc thời gian và số tiền phạt giúp vector embedding nắm bắt trọn vẹn ý định nghiệp vụ, nâng cao tối đa điểm số truy xuất.


---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn xử lý yêu cầu đổi trả là bao lâu? (Ambiguous audience) | Người mua có thể gửi yêu cầu đổi trả hoặc hoàn tiền trong vòng 7 ngày đối với hàng tiêu dùng và 30 ngày đối với đồ điện tử. | `tiki-return-policy-buyer#0` |
| 2 | Thời gian xử lý bảo hành sản phẩm gửi qua sàn TMĐT kéo dài bao nhiêu ngày? | Thời gian xử lý bảo hành khi gửi sản phẩm về kho của sàn TMĐT trung bình từ 14 đến 21 ngày làm việc. | `tiki-warranty-policy-buyer#0` |
| 3 | Nhà bán hàng bị phạt bao nhiêu tiền khi hủy đơn do hết hàng hoặc sai giá? | Nhà bán hàng bị phạt 50.000 VNĐ trên mỗi đơn hàng vi phạm do hủy đơn vì hết hàng hoặc sai giá. | `seller-return-fulfillment-rules#1` |
| 4 | Sàn TMĐT cấm đăng bán loại rượu có nồng độ cồn từ bao nhiêu độ trở lên? | Không được đăng bán rượu có nồng độ cồn từ 15 độ trở lên. Rượu dưới 15 độ phải có cảnh báo độ tuổi. | `ecommerce-prohibited-items#1` |
| 5 | Thời hạn gửi khiếu nại sau khi đơn hàng giao thành công là bao nhiêu ngày? | Người mua hoặc Nhà bán hàng có quyền khiếu nại trong vòng 30 ngày kể từ ngày đơn hàng giao thành công. | `ecommerce-dispute-resolution#1` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn xử lý yêu cầu đổi trả là bao lâu? | `search_with_filter` (`audience: buyer`) | Có (Top-1) | Lọc metadata `audience` giúp phân biệt chính xác quy định 7-30 ngày của người mua với 48h của người bán. |
| 2 | Thời gian xử lý bảo hành sản phẩm gửi qua sàn... | `RecursiveChunker` | Có (Top-1) | Giữ nguyên các mốc thời gian 14-21 ngày làm việc. |
| 3 | Nhà bán hàng bị phạt bao nhiêu tiền khi hủy đơn... | `RecursiveChunker` | Có (Top-1) | Định vị chính xác số tiền phạt 50.000 VNĐ. |
| 4 | Sàn TMĐT cấm đăng bán loại rượu có nồng độ cồn... | `SentenceChunker` | Có (Top-1) | Trích xuất chuẩn nồng độ cồn từ 15 độ trở lên. |
| 5 | Thời hạn gửi khiếu nại sau khi đơn hàng giao... | `RecursiveChunker` | Có (Top-1) | Lấy đúng thời hạn 30 ngày giải quyết tranh chấp. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata cực kỳ hữu ích và bắt buộc ở Câu hỏi #1 ("Thời hạn xử lý yêu cầu đổi trả là bao lâu?"). Nếu không dùng `metadata_filter={"audience": "buyer"}`, hệ thống sẽ trả về tài liệu xử lý đổi trả dành cho người bán (48 giờ) gây sai lệch nghiêm trọng. Việc lọc metadata giúp phân định rõ góc nhìn giữa Người mua và Nhà bán hàng trên sàn TMĐT.


---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Hiệu quả của Metadata Pre-filtering:** Metadata filtering giải quyết triệt để bài toán nhập nhằng giữa quy định cho Người mua (buyer) và Nhà bán hàng (seller) mà vector similarity đơn thuần không thể phân biệt.
> 2. **Ưu thế của Heading-based Chunking:** Chia văn bản theo các tiêu đề `#`, `##` giữ trọn vẹn ngữ cảnh của từng điều khoản pháp lý TMĐT, tránh làm vụn các con số và thời hạn quan trọng.
> 3. **Source Traceability trong RAG:** Đánh số trích dẫn `[1]`, `[2]` trong prompt giúp người dùng dễ dàng kiểm chứng nguồn gốc câu trả lời từ tài liệu gốc.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tập dữ liệu chính sách TMĐT, chiến lược `FixedSizeChunker` dễ cắt ngang giữa các câu điều khoản làm điểm truy xuất giảm nhẹ. Trong khi đó, `HeadingChunker` và `RecursiveChunker` giữ trọn vẹn cấu trúc tiêu đề và ý nghĩa đoạn văn, mang lại điểm số retrieval vượt trội.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nếu làm lại, nhóm sẽ bổ sung thêm các thuộc tính metadata chi tiết hơn như `product_category` (điện tử, gia dụng, thực phẩm) và kết hợp mã hóa lai (Hybrid Search: BM25 + Vector Embedding) để tối ưu hóa truy xuất cho các từ khóa chuyên ngành.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |


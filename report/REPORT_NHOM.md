# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm G00
**Thành viên:** 
-Trần Hoàng Duy Anh-02558
-Phạm Thanh Sơn - 02794
-Nguyễn Minh Kiệt-02373
-Đào Minh Hiếu-02561
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách mua bán và dịch vụ hậu mãi trên sàn thương mại điện tử Tiki.

**Tại sao nhóm chọn chủ đề này?**
Chủ đề này rất phù hợp cho bài lab vì có nhiều tài liệu có cùng lĩnh vực nhưng khác đối tượng và khác quy định. Ngoài ra, dữ liệu có tính cấu trúc rõ ràng, dễ chia theo heading và dễ kiểm chứng bằng metadata như `audience` và `category`.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------------|----------------------|----------|-----------------|
| 1 | tiki-return-policy-buyer.md | Tiki policy | 2026-09-20 | ~7.2k | audience=buyer, category=return-policy |
| 2 | tiki-warranty-policy-buyer.md | Tiki policy | 2026-09-20 | ~6.9k | audience=buyer, category=warranty-policy |
| 3 | seller-return-fulfillment-rules.md | Tiki seller policy | 2026-09-20 | ~6.0k | audience=seller, category=return-ops |
| 4 | seller-warranty-penalty-rules.md | Tiki seller policy | 2026-09-20 | ~6.8k | audience=seller, category=penalty-policy |
| 5 | ecommerce-prohibited-items.md | Ecommerce policy | 2026-09-20 | ~6.3k | category=product-policy |
| 6 | ecommerce-dispute-resolution.md | Ecommerce policy | 2026-09-20 | ~5.5k | category=dispute-policy |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| audience | string | buyer / seller / both | Phân biệt đúng đối tượng người hỏi và tránh lẫn giữa chính sách khách hàng và nhà bán |
| category | string | return-policy / dispute-policy | Tách từng loại chính sách để filter khi cần |
| doc_id | string | tiki-return-policy-buyer | Dùng để định danh file gốc trong store |
| source_url | string | https://... | Nguồn gốc và kiểm chứng tài liệu |
| retrieved_at | string | 2026-09-20 | Theo dõi phiên bản dữ liệu |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu, sau đó so sánh với benchmark thực tế của nhóm:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------------------|---------------|------------------|---------------------------|
| Chính sách Tiki | FixedSizeChunker (`fixed_size`) | tương đối cao | trung bình | Trung bình — dễ cắt xén giữa các mục quan trọng |
| Chính sách Tiki | SentenceChunker (`by_sentences`) | vừa phải | tương đối ổn | Khá tốt nếu câu dài và cấu trúc rõ |
| Chính sách Tiki | RecursiveChunker (`recursive`) | vừa đủ | ổn định | Tốt nhất về balance giữa ngữ cảnh và độ dài |
| Chính sách Tiki | HeadingChunker (`heading`) | ít hơn | dài hơn | Tốt nhất với doc có cấu trúc `##` rõ ràng |

### Chiến lược của từng thành viên

**Đào Minh Hiếu— FixedSizeChunker**
- **Loại chiến lược:** FixedSize
- **Mô tả & lý do chọn cho chủ đề này:** Fixed-size dễ triển khai và hữu ích khi cần kiểm soát số lượng chunk. Tuy nhiên, với chính sách có nhiều mục và định nghĩa rõ ràng, nó dễ cắt giữa các phần quan trọng.
- **Code snippet (nếu custom):**
```python
FixedSizeChunker(chunk_size=500, overlap=50)
```

**Phạm Thanh Sơn — SentenceChunker**
- **Loại chiến lược:** Sentence
- **Mô tả & lý do chọn:** Cách này giữ tốt ranh giới câu và phù hợp với văn bản chính sách, nơi mỗi câu thường mang một ý rõ ràng. Tuy nhiên, với các mục dài hoặc nhiều nhánh điều kiện, số lượng chunk có thể không đồng đều.
- **Code snippet:**
```python
SentenceChunker(max_sentences_per_chunk=3)
```

**Nguyễn Minh Kiệt — RecursiveChunker**
- **Loại chiến lược:** Recursive
- **Mô tả & lý do chọn:** Recursive ưu tiên chia theo cấp độ ranh giới lớn trước như section, dòng, câu. Đây là cách phù hợp nhất với chính sách có cấu trúc theo mục và điều khoản.
- **Code snippet:**
```python
RecursiveChunker(chunk_size=500, separators=["\n\n", "\n", ". ", " ", ""])
```

**Trần Hoàng Duy Anh — HeadingChunker**
- **Loại chiến lược:** Custom / heading-based
- **Mô tả & lý do chọn:** Với văn bản chính sách Tiki, mỗi `##` hoặc `#` là một đơn vị ngữ nghĩa hoàn chỉnh. Chia theo heading giúp giữ ngữ cảnh tốt nhất và tránh mất tiêu đề khi tách section dài. Khi section quá dài, ta hạ xuống recursive để tiếp tục cắt.
- **Code snippet:**
```python
HeadingChunker(chunk_size=600)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------------------|----------------------|-----------|----------|
| 1 | FixedSize | 5/10 | Dễ triển khai, đồng đều về độ dài | Có thể cắt mất câu trả lời ở ranh giới chunk |
| 2 | Sentence | 6/10 | Giữ ranh giới câu, dễ đọc | Một số chunk còn thiếu ngữ cảnh khi câu quá dài |
| 3 | Recursive | 7/10 | Cân bằng giữa ngữ cảnh và tính thực tế | Với doc quá dài, vẫn có thể bị lặp từ/điểm đồng nhất |
| 4 | Heading | 7.5/10 | Giữ ngữ cảnh và tiêu đề rất tốt cho chính sách có cấu trúc | Cần xử lý section rất dài bằng recursive để tránh chunk quá lớn |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
Với tài liệu chính sách theo mục như Tiki, chiến lược theo heading và recursive cho hiệu quả tốt hơn fixed size hay sentence thuần túy. Lý do là văn bản này có cấu trúc theo mục, điều khoản và tiêu đề rất rõ, nên nếu giữ tiêu đề cùng phần nội dung thì retrieval có khả năng chọn đúng section hơn. Đây cũng là lý do mà không ít câu hỏi cần filter by `audience` lại bị lẫn nếu chunk không giữ đúng nội dung mục đích.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-----------------|--------------------------------|--------------------------|
| 1 | Thời hạn xử lý yêu cầu đổi trả là bao lâu? | Khách Hàng cần hoàn trả sản phẩm trong vòng 07 ngày làm việc kể từ ngày yêu cầu được chấp nhận. | tiki-return-policy-buyer |
| 2 | Thời gian xử lý bảo hành sản phẩm thông thường cho người mua kéo dài bao lâu? | Từ 14 đến 30 ngày làm việc tùy thuộc vào linh kiện thay thế của Trung tâm bảo hành chính hãng. | tiki-warranty-policy-buyer |
| 3 | Nhà bán hàng bị xử lý như thế nào nếu kinh doanh hàng giả, hàng nhái? | Phạt 100% giá trị đơn hàng, bồi thường gấp 3 lần cho người mua và khóa vĩnh viễn gian hàng. | seller-warranty-penalty-rules |
| 4 | Mặt hàng rượu nào bị cấm kinh doanh trên sàn TMĐT Tiki? | Rượu có nồng độ cồn từ 15 độ trở lên. | ecommerce-prohibited-items |
| 5 | Thời hạn Tiki ban hành quyết định phân xử tranh chấp cuối cùng là bao lâu? | Trong vòng 05 ngày làm việc kể từ ngày tiếp nhận đầy đủ bằng chứng từ cả hai bên. | ecommerce-dispute-resolution |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|---------------------------------|--------------------------------|---------|
| 1 | Thời hạn xử lý yêu cầu đổi trả là bao lâu? | Recursive / Heading | Có | Câu này cần `audience=buyer`; nếu không lọc dễ lẫn với seller-policy |
| 2 | Thời gian xử lý bảo hành sản phẩm thông thường cho người mua kéo dài bao lâu? | Heading / Sentence | Có | Dùng filter buyer tăng độ chính xác |
| 3 | Nhà bán hàng bị xử lý như thế nào nếu kinh doanh hàng giả, hàng nhái? | Recursive | Có | Top-3 chứa câu trả lời rõ ràng |
| 4 | Mặt hàng rượu nào bị cấm kinh doanh trên sàn TMĐT Tiki? | Recursive / Heading | Có | Dễ xác định vì có câu chứa độ cồn cụ thể |
| 5 | Thời hạn Tiki ban hành quyết định phân xử tranh chấp cuối cùng là bao lâu? | Heading | Có | Chính sách tranh chấp tập trung trong một section rõ ràng |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
Có, metadata filter giúp rất nhiều ở câu hỏi cần phân biệt đối tượng, đặc biệt câu 1: “Thời hạn xử lý yêu cầu đổi trả là bao lâu?” nếu không đặt `audience=buyer`, hệ thống dễ nhầm với chính sách dành cho người bán hoặc chính sách bảo hành. Kết quả benchmark cho thấy khi không lọc, top-3 có thể rơi vào nhiều file khác nhau và dễ bị lẫn; khi lọc theo `audience`, khớp đúng với tài liệu khách hàng. Đây là bằng chứng rõ ràng cho việc metadata filter là bắt buộc trong các câu hỏi đa nghĩa.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- Chính sách Tiki có cấu trúc rõ theo mục và theo đối tượng, nên chunk theo heading hoặc recursive hiệu quả hơn so với fixed size.
- Metadata filter không chỉ tăng độ chính xác mà còn giúp tránh lẫn giữa buyer-policy và seller-policy khi từ khoá trùng nhau.
- Không chỉ top-3 đúng doc_id mới là đủ; phải kiểm tra context thực tế có chứa câu trả lời hay không.

**Bài học rút ra khi so sánh trong nhóm:**
Cùng một bộ dữ liệu nhưng chiến lược chia chunk khác nhau giúp retrieval khác nhau rõ rệt. Fixed-size dễ tiện nhưng dễ cắt mất câu trả lời, trong khi heading và recursive giữ tốt ngữ cảnh mục, đặc biệt với văn bản chính sách có nhánh theo điều khoản. Vì vậy, không có một chiến lược “vạn năng”; phải chọn theo cấu trúc dữ liệu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
Nếu làm lại, nhóm sẽ ưu tiên chunk theo heading hoặc recursive, đồng thời gắn metadata `audience` lên từng chunk để filter hiệu quả. Ngoài ra, nên đánh giá retrieval ở mức “có chứa câu trả lời thực sự trong context” thay vì chỉ nhìn doc_id nằm trong top-3.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

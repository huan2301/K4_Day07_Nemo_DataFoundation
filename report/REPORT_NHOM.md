# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nemo
**Thành viên:**
| Họ và tên | Mã học viên |
|---|---|
| Nguyễn Ngọc Huân | 2A202601164 |
| Lê Đình Việt | 2A202601528 |
| Quách Thanh Hưng| 2A202601532 |
| Vương Đức Thoại | 2A202601770 |

**Ngày nộp:** 03-08-2026

> Báo cáo nhóm theo cấu trúc mẫu cung cấp. Tài liệu, cấu hình và kết quả benchmark được lấy trực tiếp từ repository (thư mục `data/k4_ecommerce`, script `ingest.py`, và benchmark `data/k4_ecommerce/benchmark_queries.json`). Mọi số liệu đều là kết quả chạy thực tế trên code nguồn trong repo (sử dụng `_mock_embed` trừ khi ghi chú khác).

---

## 1. Lựa chọn tài liệu (Document Set Quality)

### 1.1 Phạm vi bộ tài liệu
Nhóm chọn chủ đề: chính sách thương mại điện tử và hỗ trợ khách hàng (Shopify, eBay) — tập trung vào các chính sách trả hàng/hoàn tiền, thanh toán, dịch vụ khách hàng và chính sách của Google Merchant. Bộ tài liệu nằm trong `data/k4_ecommerce` và gồm các trang help center công khai của các nền tảng liên quan.

### 1.2 Danh sách tài liệu (Data inventory)
Danh sách tài liệu (lấy từ `data/k4_ecommerce/sources.csv`):

| # | doc_id | File | Title | Source URL | retrieved_at |
|---|--------|------|-------|------------|--------------|
| 1 | k4-ebay-return-policy | data/k4_ecommerce/k4-ebay-return-policy.md | eBay — Return policy (help) | https://www.ebay.com/help/selling/returns-refunds/return-policy?id=4260 | 2026-08-03 |
| 2 | k4-google-merchant-policy | data/k4_ecommerce/k4-google-merchant-policy.md | Google Merchant Center — policies | https://support.google.com/merchants/answer/6150127 | 2026-08-03 |
| 3 | k4-shopify-customer-service | data/k4_ecommerce/k4-shopify-customer-service.md | Shopify — Providing online customer service | https://help.shopify.com/en/manual/customers/customer-service | 2026-08-03 |
| 4 | k4-shopify-payments | data/k4_ecommerce/k4-shopify-payments.md | Shopify — Payments | https://help.shopify.com/en/manual/payments | 2026-08-03 |
| 5 | k4-shopify-returns | data/k4_ecommerce/k4-shopify-returns.md | Shopify — Order management (returns & refunds) | https://help.shopify.com/en/manual/orders/returns-and-refunds | 2026-08-03 |

Tất cả nguồn đều là tài liệu công khai (help center) — phù hợp để sử dụng làm corpus cho bài lab.

### 1.3 Metadata schema
Khi ingest, `ingest.py` gắn front matter vào từng Document và sau đó `chunk_document()` bổ sung metadata cho từng chunk. Metadata chính (present / used):

- doc_id (string): identifier document gốc. Quan trọng để nhóm và để delete_document.
- source (string): đường dẫn file nguồn trong repository (traceability).
- retrieved_at (date): ngày thu thập nguồn (từ sources.csv front-matter).
- chunk_index (int): vị trí chunk trong document — cho phép mở lại chỗ gốc.
- customer_role (optional): trường dữ liệu trong front-matter (ví dụ buyer/seller/both) — dùng cho filter trong benchmark.

**Tại sao metadata hữu ích cho retrieval?**
- Cho phép lọc theo phạm vi (ví dụ chỉ tìm thông tin hướng tới `buyer`) trước khi thực hiện xếp hạng, nâng tỉ lệ trả về kết quả liên quan.
- Cung cấp provenance để giải thích kết quả (nguồn, vị trí chunk).
- Hỗ trợ các thao tác quản trị như xóa toàn bộ chunks của một document.

---

## 2. Thiết kế chiến lược (Strategy Design)

Nhóm phân công mỗi thành viên thử một chiến lược chunking khác nhau (hoặc cùng chỉnh tham số) để so sánh trên cùng corpus.

### Thành viên & phân công
- Nguyễn Ngọc Huân
  - Vai trò: thiết lập và chạy chiến lược RecursiveChunker; thu thập kết quả benchmark và phân tích precision@k.
  - Strategy: RecursiveChunker
  - Configuration:
    - chunk_size: 400
    - separators: ["\n## ", "\n# ", "\n\n", "\n", ". ", " "]
  - Lý do chọn: ưu tiên giữ ranh giới cấu trúc (headings / paragraphs) trước khi phân tách nhỏ hơn; phù hợp với tài liệu help center có nhiều đoạn và tiêu đề.
  - Điểm mạnh: giữ được ngữ cảnh, số lượng chunk vừa phải, dễ truy xuất thông tin theo heading.
  - Điểm yếu: với nội dung ít phân đoạn, có thể dẫn tới chunk lớn hơn mong muốn; cần điều chỉnh separators/ chunk_size.
  - Ảnh hưởng tới RAG: tạo context mạch lạc hơn, giúp agent trả lời dựa trên đoạn văn nguyên vẹn.

- Lê Đình Việt
  - Vai trò: chạy SentenceChunker và đánh giá sự khác biệt về coherence của chunks.
  - Strategy: SentenceChunker
  - Configuration:
    - max_sentences_per_chunk: 3 (mặc định thử nghiệm)
  - Lý do chọn: SentenceChunker giữ ranh giới ngôn ngữ tự nhiên, phù hợp cho FAQ và các câu hỏi ngắn.
  - Điểm mạnh: tạo chunk dễ đọc, ít bị cắt giữa câu.
  - Điểm yếu: kích thước chunk không đồng đều; có thể tạo chunk quá dài (nếu nhiều câu dài), làm embedding kém hiệu quả.
  - Ảnh hưởng tới RAG: tốt cho câu hỏi ngắn, nhưng khi chunk quá dài có thể giảm hiệu quả ranking.

- Vương Đức Thoại
  - Vai trò: thử FixedSizeChunker, kiểm tra ảnh hưởng của overlap vào recall.
  - Strategy: FixedSizeChunker
  - Configuration:
    - chunk_size: 500
    - overlap: 50
  - Lý do chọn: baseline đơn giản, dễ dự đoán số chunk; overlap giúp giữ ngữ cảnh xuyên chunk.
  - Điểm mạnh: dễ reproduce, kiểm soát kích thước chunk rõ ràng.
  - Điểm yếu: cắt ngang câu/ý nghĩa, cần overlap điều chỉnh cẩn trọng.
  - Ảnh hưởng tới RAG: thường tăng recall (nếu thông tin nằm trên ranh giới), nhưng có thể giảm precision do nhiều chunk có nội dung trùng nhau.

- Quách Thanh Hưng 
  - Vai trò: so sánh cấu hình FixedSize/Sentence/Recursive; thu thập logs lỗi và chạy benchmark metadata filters.
  - Strategy: FixedSize (experiment) — proxy cho member 3 ở hiện trạng repo
  - Configuration:
    - chunk_size: 500
    - overlap: 50
  - Lý do chọn: thử nghiệm practical baseline và kiểm tra search_with_filter behaviour.
  - Điểm mạnh: dễ tối ưu tham số overlap để tăng recall cho policy-related queries.
  - Điểm yếu: thiếu ranh giới ngữ nghĩa, cần ghép thêm logic để preserve sentences.
  - Ảnh hưởng tới RAG: nếu overlap lớn, agent có thể truy tiếp nhiều đoạn chồng lặp, gây lặp thông tin trong prompt.

### 2.1 Baseline phân tích (Chunking strategy comparator)
Chạy `ChunkingStrategyComparator().compare()` trên toàn bộ 5 tài liệu (chunk_size=400) thu được số liệu tóm tắt (count / avg_length):

- k4-ebay-return-policy:
  - fixed_size: count=2, avg_length=324
  - by_sentences: count=1, avg_length=646
  - recursive: count=2, avg_length=322.5

- k4-google-merchant-policy:
  - fixed_size: count=3, avg_length=281
  - by_sentences: count=1, avg_length=840
  - recursive: count=3, avg_length=279.33

- k4-shopify-customer-service:
  - fixed_size: count=3, avg_length=358.33
  - by_sentences: count=1, avg_length=1071
  - recursive: count=4, avg_length=267

- k4-shopify-payments:
  - fixed_size: count=2, avg_length=381.5
  - by_sentences: count=1, avg_length=760
  - recursive: count=3, avg_length=252.67

- k4-shopify-returns:
  - fixed_size: count=3, avg_length=375
  - by_sentences: count=1, avg_length=1122
  - recursive: count=3, avg_length=373.33

**Nhận xét:** SentenceChunker mặc định tạo rất ít chunk (thường 1) cho các trang dài, dẫn tới chunk dài vượt kích thước mục tiêu. RecursiveChunker thể hiện cân bằng tốt hơn cho corpus này.

---

## 3. Retrieval Quality (Benchmark)

### 3.1 Dữ liệu benchmark
File benchmark queries: `data/k4_ecommerce/benchmark_queries.json` (5 queries). Mỗi query gồm id, question, gold_document, expected_chunk, và metadata_filter (nếu có). Benchmark của nhóm sử dụng `_mock_embed` (mặc định trong repository) để đảm bảo tính tái lập cho unit tests.

### 3.2 Kết quả chạy thực tế (tóm tắt)
Chạy benchmark cho 3 cấu hình thành viên (cấu hình lưu trong `report/team_chunkers.yaml`), lưu kết quả vào `report/team_bench_results.json`. Tóm tắt kết quả (top-3 doc_ids cho mỗi query):

Tổng chunks đã load (per member):
- Nguyễn Ngọc Huân (RecursiveChunker): 67 chunks
- Lê Đình Việt (SentenceChunker): 40 chunks
- Quách Thanh Hưng (FixedSizeChunker): 41 chunks

Tổng quan accuracy (gold_document có trong top-3):
- Nguyễn Ngọc Huân: 5/5
- Lê Đình Việt: 5/5
- Quách Thanh Hưng: 5/5

(Nhưng precision@1 thấp: top-1 thường không phải gold — chi tiết bên dưới.)

### 3.3 Bảng chi tiết (mỗi query)
Dưới đây là bảng tóm tắt 5 câu hỏi benchmark, câu trả lời gold (gold_answer từ JSON), document vàng (gold_document), và kết quả retrieval ví dụ (Member Huân / Việt / Hưng — top-1..top-3 doc_ids). Score không được xuất bởi script đơn giản (dot product raw values) — nếu cần có thể mở rộng script để lưu score numeric.

| ID | Query | Gold doc | Gold answer (short) | Top-3 (Huân) | Top-3 (Việt) | Top-3 (Hưng) |
|---|-------|----------|----------------------|--------------|--------------|--------------|
| Q1 | How can a Shopify merchant issue a refund for an order? | k4-shopify-returns | You can issue refunds or cancel orders via Orders admin. | [k4-ebay-return-policy, k4-shopify-returns, k4-shopify-returns] | [k4-ebay-return-policy, k4-shopify-returns, k4-ebay-return-policy] | [k4-shopify-returns, k4-ebay-return-policy, k4-shopify-returns] |
| Q2 | What payment methods can customers use on a Shopify store? | k4-shopify-payments | Shopify Payments, third-party providers, accelerated checkouts. | [k4-shopify-customer-service, k4-shopify-payments, k4-shopify-payments] | [k4-shopify-payments, k4-shopify-payments, k4-shopify-payments] | [k4-shopify-customer-service, k4-shopify-payments, k4-shopify-payments] |
| Q3 | What practices can lead to account suspension under Google Merchant Center policies? | k4-google-merchant-policy | Misrepresentation, hiding costs, unclear returns, unavailable products; may lead to suspension. | [k4-google-merchant-policy, k4-google-merchant-policy] | [k4-google-merchant-policy, k4-google-merchant-policy] | [k4-google-merchant-policy, k4-google-merchant-policy] |
| Q4 | What customer service practices does Shopify recommend? | k4-shopify-customer-service | Set clear policies, multiple contact channels, use messaging tools. | [k4-shopify-payments, k4-shopify-payments, k4-shopify-customer-service] | [k4-shopify-payments, k4-shopify-customer-service, k4-shopify-customer-service] | [k4-shopify-payments, k4-shopify-customer-service, k4-shopify-payments] |
| Q5 | What should I know about return policies? | k4-ebay-return-policy | Sellers must follow eBay rules and buyers can request returns per policy. | [k4-shopify-returns, k4-ebay-return-policy, k4-shopify-returns] | [k4-shopify-returns, k4-ebay-return-policy, k4-ebay-return-policy] | [k4-ebay-return-policy, k4-shopify-returns, k4-shopify-returns] |

**Quan sát:**
- Tất cả thành viên đều có gold_document nằm trong top-3 cho 5 query (precision@3 = 100%).
- Tuy nhiên precision@1 (top-1) thấp: nhiều trường hợp top-1 là tài liệu có từ khoá tương đồng (ví dụ Q1 top-1 là eBay return policy) — có thể gây nhầm lẫn khi chỉ dựa trên top-1.
- Một số truy vấn dạng filtering (metadata_filter) như Q1/Q3/Q5 yêu cầu metadata (customer_role) để ưu tiên kết quả phù hợp; nếu metadata_filter được cung cấp chính xác, top-ranked candidates cải thiện.

### 3.4 Failure analysis (chọn 2 case)

Case A — Q1 (Refunds)
- Triệu chứng: một số cấu hình trả về `k4-ebay-return-policy` ở vị trí top-1 thay vì `k4-shopify-returns` (gold).
- Nguyên nhân khả dĩ:
  - `_mock_embed` dùng trong benchmark không phản ánh semantic tốt cho domain; embedding chủ yếu deterministic nhưng không semantically rich.
  - Các văn bản về refund/returns của eBay và Shopify chia sẻ nhiều từ khóa tương tự (refund, return), dẫn tới dot-product cao với query.
  - Thiếu hoặc không dùng metadata_filter (`customer_role`) làm tăng khả năng trộn lẫn các tài liệu hướng tới seller/buyer.
- Biện pháp khắc phục:
  - Sử dụng embedder đa ngữ thật (LocalEmbedder) để có embedding semantic tốt hơn.
  - Dùng thêm step reranker (ví dụ cross-encoder) trên top-N để chọn chunk thật chứa gold answer.
  - Kiểm soát chunk boundaries (increase overlap hoặc prefer sentence boundaries) để preserve câu chứa term then action.

Case B — Q4 (Customer service best practices)
- Triệu chứng: top-1 nhiều khi là `k4-shopify-payments` (liên quan đến payment) thay vì `k4-shopify-customer-service`.
- Nguyên nhân:
  - Từ khóa chung (shipping, payments, contact) xuyên tài liệu; dot-product dựa vào từ khóa chiếm ưu thế khi embedding thiếu độ phân biệt.
  - Chunking config (FixedSize or Recursive with certain separators) có thể split heading/section dẫn tới loss of contextual signals.
- Biện pháp:
  - Tinh chỉnh chunker để ưu tiên heading/section (RecursiveChunker với heading separators) — tăng chance capture toàn bộ đoạn best-practice.
  - Thêm metadata tagging (e.g., category: payments / customer_service) khi ingest nếu có thể phân loại nguồn trước.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- RecursiveChunker thường cân bằng tốt giữa giữ ngữ cảnh (preserve sections/headings) và tạo số lượng chunk hợp lý cho retrieval; nhóm sẽ minh họa bằng ví dụ trước/sau chunking.
- Vai trò của metadata (ví dụ `customer_role`) trong cải thiện precision cho các truy vấn hướng tới người mua/ người bán — sẽ trình bày case Q1/Q5 để chứng minh lợi ích filter trước khi ranking.
- Tương quan giữa chunk_size/overlap và precision@1: ví dụ thay đổi overlap cho FixedSizeChunker và quan sát top-1 aliasing.

**Bài học rút ra khi so sánh trong nhóm:**
- Cùng một corpus, chiến lược chunking ảnh hưởng trực tiếp tới chất lượng context mà agent sử dụng: RecursiveChunker giữ cấu trúc giúp trả lời chính xác hơn cho các câu hỏi theo section, trong khi FixedSize có thể tăng recall nhưng giảm precision do cắt ngang ý.
- SentenceChunker giúp nội dung dễ đọc nhưng dễ tạo chunk quá dài trên tài liệu dạng dài, dẫn tới embedding ít phân biệt hơn; do đó tham số (max_sentences_per_chunk) cần được điều chỉnh theo đặc tính nguồn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
- Chạy benchmark song song với `LocalEmbedder` (sentence-transformers) để có kết luận thực nghiệm về semantic retrieval; đưa reranker (cross-encoder) vào pipeline để cải thiện precision@1.
- Mở rộng schema metadata (category, estimated_section, language) và thêm bước tự động tagging khi ingest để hỗ trợ filter và reranking.
- Thực hiện thí nghiệm hệ thống: grid search trên chunk_size và overlap, đánh giá precision@1/3 và avg answer quality để chọn tham số tối ưu cho từng loại tài liệu.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 15 / 15 |
| Chất lượng truy xuất | 10 / 10 |
| Chuẩn bị thuyết trình/demo | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |


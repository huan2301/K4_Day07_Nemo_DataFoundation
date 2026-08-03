# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Quách Thanh Hưng
**Nhóm:** Nemo
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai embedding có hướng gần nhau trong không gian vector, nên hai câu thường nói về ý hoặc chủ đề tương tự. Điểm cao là tín hiệu xếp hạng, không tự nó chứng minh câu trả lời là đúng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền cho đơn hàng.
- Câu B: Người mua có thể nhận tiền hoàn lại khi trả hàng.
- Tại sao tương đồng: Cả hai đều diễn đạt quyền nhận refund/hoàn tiền trong bối cảnh mua hàng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hôm nay trời mưa rất to.
- Câu B: Khách hàng có thể yêu cầu hoàn tiền cho đơn hàng.
- Tại sao khác: Hai câu không có chủ đề, thực thể hoặc mục đích thông tin chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine so sánh hướng của vector thay vì độ lớn. Với text embedding, độ dài câu hoặc độ lớn vector không nên làm hai câu kém giống nhau; điều quan trọng là hướng ngữ nghĩa. Euclidean distance nhạy hơn với độ lớn nên thường kém phù hợp hơn cho việc xếp hạng semantic retrieval.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23` chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25` chunks. Overlap lớn tạo nhiều chunk hơn vì bước dịch nhỏ hơn; đổi lại, câu hoặc điều kiện nằm ở ranh giới có cơ hội xuất hiện trong cả hai chunk, giúp giữ ngữ cảnh cho retrieval.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng `re.split(r"(?<=[.!?])\s+", text.strip())` để tách sau dấu kết thúc câu rồi bỏ khoảng trắng dư ở mỗi câu. Các câu được gom theo `max_sentences_per_chunk`; chuỗi rỗng trả về danh sách rỗng và giá trị giới hạn nhỏ hơn 1 được chuẩn hóa thành 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` chọn separator theo thứ tự ưu tiên, gom các segment còn vừa `chunk_size`, và chỉ đệ quy những segment quá dài với separator còn lại. Base case là đoạn đã không vượt `chunk_size`; khi hết separator, hàm cắt theo ký tự để luôn tạo được chunk hữu hạn. `chunk_size <= 0` bị từ chối để tránh vòng lặp hoặc range không hợp lệ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hóa thành record gồm `id`, `content`, `metadata` và embedding; metadata luôn có `doc_id` để truy vết file gốc. Với backend in-memory, query được embed rồi tính dot product với từng embedding đã lưu, sắp xếp giảm dần theo score và trả tối đa `top_k` kết quả. Nếu ChromaDB có sẵn, store dùng collection của Chroma với embedding đã tạo.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata trước rồi mới xếp hạng các record còn lại; cách này tránh kết quả sai vai trò như seller/buyer. `delete_document` xóa toàn bộ record có `metadata['doc_id']` khớp, thay vì chỉ xóa một chunk `Document.id`, nên xử lý đúng tài liệu đã chia nhiều chunk.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunk, nối phần `content` bằng dòng trống và đưa vào prompt theo cấu trúc `Context`, `Question`, `Answer`. Prompt yêu cầu chỉ trả lời từ context và nói rõ khi không đủ dữ liệu; agent cũng nhận `metadata_filter` tùy chọn để context của câu trả lời khớp với retrieval đã lọc.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
42 passed in 0.05s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể yêu cầu hoàn tiền cho đơn hàng. | Người mua có thể nhận tiền hoàn lại khi trả hàng. | cao | 0.7492 | Có |
| 2 | Người bán phải công khai chính sách đổi trả. | Merchant needs to disclose the return policy. | cao | 0.7703 | Có |
| 3 | Cửa hàng hỗ trợ khách hàng qua chat và email. | Người bán nên cung cấp nhiều kênh liên hệ cho khách hàng. | cao | 0.5797 | Có |
| 4 | Hôm nay trời mưa rất to. | Khách hàng có thể yêu cầu hoàn tiền cho đơn hàng. | thấp | -0.0493 | Có |
| 5 | Khách hàng có thể thanh toán bằng PayPal. | Vi phạm chính sách có thể khiến tài khoản bị đình chỉ. | thấp | 0.1919 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 thấp hơn hai cặp cùng nghĩa rõ rệt dù vẫn cùng chủ đề customer service. Điều này cho thấy embedding biểu diễn mức độ gần nghĩa và cách diễn đạt, không chỉ nhận diện từ khóa. Cặp 5 có điểm dương nhỏ dù hai câu khác ý, vì cùng nằm trong domain thương mại điện tử; vì thế không thể dùng score cao/thấp thay cho kiểm tra evidence trong chunk.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How can a Shopify merchant issue a refund for an order? | `k4-shopify-returns`, chunk 1: workflow quản lý đơn và câu về issue refunds/cancel orders. | 0.1658 | Có, top-1 chứa evidence của gold answer. | Báo thiếu dữ liệu; không trả lời đầy đủ dù context liên quan. |
| 2 | What payment methods can customers use on a Shopify store? | `k4-shopify-payments`, chunk 0: Shopify Payments, third-party providers và accelerated checkouts. | 0.1334 | Có, top-1 chứa evidence của gold answer. | Báo thiếu dữ liệu; không liệt kê các payment method. |
| 3 | What practices can lead to account suspension under Google Merchant Center policies? | `shopify-markets`, chunk 1: cấu hình market và return/refund settings. | 0.0891 | Không; không có Google Merchant policy hoặc account suspension trong top-3. | Báo thiếu dữ liệu, phù hợp với context không có bằng chứng. |
| 4 | What customer service practices does Shopify recommend? | `k4-shopify-payments`, chunk 0: payment methods, không phải danh sách customer-service practices. | 0.1450 | Không; chunk customer-service ở rank 2 chỉ là phần giới thiệu, không chứa danh sách gold practices. | Báo thiếu dữ liệu; context không đủ chi tiết để trả lời gold answer. |
| 5 | What should I know about return policies? | `k4-shopify-returns`, chunk 1: thông tin returns của Shopify, không phải gold eBay. Gold `k4-ebay-return-policy`, chunk 0 ở rank 3. | 0.3169 | Có ở top-3 (rank 3) vì chunk eBay chứa seller/buyer responsibilities và returns. | Báo thiếu dữ liệu; không tổng hợp được evidence từ rank 3. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng phải chấm ở mức chunk, không chỉ kiểm tra `doc_id`: Q4 có đúng tài liệu customer-service trong top-3 nhưng chunk được truy xuất không chứa danh sách thực hành trong gold answer. Tôi cũng nhận ra cùng corpus và cùng embedder là điều kiện bắt buộc để so sánh strategy; mock embedding chỉ kiểm tra luồng kỹ thuật, còn benchmark semantic cần local multilingual embedder.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 |
| **Tổng phần cá nhân** | **53 / 60** |

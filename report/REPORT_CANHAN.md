# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vương Đức Thoại
**Nhóm:** Nemo
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau. Điều này thường cho thấy hai đoạn văn bản có nội dung hoặc ý nghĩa tương đồng, ngay cả khi sử dụng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền cho sản phẩm bị lỗi.
- Câu B: Người mua được phép đề nghị hoàn tiền khi sản phẩm có khuyết điểm.
- Tại sao tương đồng: Hai câu sử dụng từ ngữ khác nhau nhưng đều nói về quyền yêu cầu hoàn tiền khi sản phẩm bị lỗi.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền cho sản phẩm bị lỗi.
- Câu B: Thời tiết hôm nay có mưa lớn.
- Tại sao khác: Hai cầu đề cập đến hai chủ đề hoàn toàn khác nhau. một câu về chính sách hoàn tiền, còn câu kia nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của các vector nên phản ánh tốt hơn mức độ tương đồng về ngữ nghĩa và ít bị ảnh hưởng bởi đồ lớn của vector. Trong khi đó, khoảng cách Euclid phụ thuộc cả hướng lẫn độ lớn nên hai văn bản gần nghĩa vẫn có thể bị đánh giá là cách xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước dịch chuyển giữa hai chunk liên tiếp là `chunk_size - overlap = 500 - 50 = 450`.Số chunk được tính băng:
> 
> `ceil((document_length - overlap) / (chunk_size - overlap))`
> `= ceil((10,000 - 50) / (500 - 50))`
> `= ceil(9,950 / 450)`
> `= ceil(22.11)`
> `= 23`
> *Đáp án:* Tài liệu được chia thành **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap=100`, bước dịch chuyển còn `500 - 100 = 400` ký tự và số chunk là `ceil((10,000 - 100) / 400)` = ceil(24,75) = 25`, tức tăng từ 23 lên 25 chunks. Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh tại ranh giới giữa hai chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy `r"(?<=[.!?])\s+"` để tách văn bản tại khoảng trắng đứng sau các dấu kết thúc câu `.`, `!` hoặc `?`, nhờ đó dấu câu vẫn được giữ lại ở cuối câu phía trước. Sau khi tách, tôi dùng `strip()` để loại bỏ khoảng trắng thừa và bỏ các chuỗi rỗng, sau đó gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk; nếu đầu vào rỗng thì trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*
> Tôi chia văn bản đệ quy theo thứ tự ưu tiên của các ranh giới tự nhiên: đoạn văn `"\n\n"`, dòng `"\n"`, câu `". "`, từ `" "` và cuối cùng là ký tự `""`. Base case là khi văn bản đã ngắn hơn hoặc bằng `chunk_size` thì trả về ngay; nếu không còn separator phù hợp thì cắt cố định theo `chunk_size`, còn những phần vẫn quá dài sẽ tiếp tục được xử lý bằng separator có mức ưu tiên thấp hơn.


### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*
> Trong `add_documents`, tôi tạo embedding từ `content` của từng `Document`, sau đó lưu một record gồm ID duy nhất, nội dung, metadata và embedding vào bộ nhớ hoặc ChromaDB nếu thư viện này khả dụng. Trong `search`, câu truy vấn được chuyển thành embedding, tính điểm tương đồng với từng record bằng tích vô hướng (dot product), sau đó sắp xếp theo điểm giảm dần và trả về `top_k` kết quả tốt nhất.


**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*
> Với `search_with_filter`, tôi lọc các record theo metadata trước, bằng cách kiểm tra tất cả cặp key-value trong `metadata_filter`, rồi mới tính độ tương đồng trên tập kết quả đã lọc. Với `delete_document`, tôi xóa tất cả chunk có `metadata["doc_id"]` trùng với `doc_id` được yêu cầu và trả về `True` nếu có ít nhất một chunk bị xóa, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*
> Trong `answer`, tôi dùng câu hỏi để truy xuất `top_k` chunk liên quan nhất từ `EmbeddingStore`, sau đó nối nội dung các chunk thành một phần ngữ cảnh có đánh số hoặc phân cách rõ ràng. Tôi tạo prompt gồm ngữ cảnh, câu hỏi và chỉ dẫn cho mô hình chỉ trả lời dựa trên thông tin được cung cấp; cuối cùng truyền prompt vào `llm_fn` và trả về kết quả của mô hình.
---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How can a Shopify merchant issue a refund for an order? | `k4-ebay-return-policy::chunk_0` — nội dung chung về đổi trả eBay, không chứa quy trình refund Shopify | 0.1415 | Không; chunk có bằng chứng nằm hạng 2 | Demo stub chỉ xác minh prompt/RAG, chưa chấm chất lượng câu trả lời |
| 2 | What payment methods can customers use on a Shopify store? | `k4-shopify-customer-service::chunk_0` — giới thiệu trải nghiệm chăm sóc khách hàng | 0.1772 | Không; chunk payment có bằng chứng nằm hạng 2 | Demo stub chỉ xác minh prompt/RAG, chưa chấm chất lượng câu trả lời |
| 3 | What practices can lead to account suspension under Google Merchant Center policies? | `k4-google-merchant-policy::chunk_1` — best practices nhưng không chứa điều kiện suspension | -0.0434 | Không; chunk có bằng chứng nằm hạng 2 | Demo stub chỉ xác minh prompt/RAG, chưa chấm chất lượng câu trả lời |
| 4 | What customer service practices does Shopify recommend? | `k4-shopify-payments::chunk_0` — phương thức thanh toán, không chứa customer-service practices | 0.1329 | Không; chunk có bằng chứng nằm hạng 3 | Demo stub chỉ xác minh prompt/RAG, chưa chấm chất lượng câu trả lời |
| 5 | What should I know about return policies? | `k4-shopify-returns::chunk_0` — chỉ là heading đổi trả Shopify | 0.2371 | Không; chunk eBay có bằng chứng nằm hạng 2 | Demo stub chỉ xác minh prompt/RAG, chưa chấm chất lượng câu trả lời |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

> **Giới hạn phép đo:** Kết quả trên dùng `MockEmbedder`, vì vậy chỉ xác minh luồng kỹ thuật, chunking, metadata và provenance; không dùng để kết luận chất lượng ngữ nghĩa hay strategy tốt nhất. Báo cáo chi tiết từng top-3 chunk và A/B filter nằm trong `report/BENCHMARK_VUONG_DUC_THOAI.md`.

**A/B metadata filter:** Với query 5, cả hai lần chạy có và không có `customer_role=buyer` đều đưa chunk chứa bằng chứng eBay lên hạng 2. Filter loại tài liệu `both` như Shopify Payments khỏi top-3 nhưng chưa cải thiện thứ hạng evidence, cho thấy metadata tăng precision theo vai trò nhưng không tự giải quyết lỗi ranking.

**Failure case:** Query 1 trả `k4-ebay-return-policy::chunk_0` ở top-1 dù bằng chứng cần thiết nằm trong `k4-shopify-returns::chunk_1` ở hạng 2; có 2/3 chunk top-3 không chứa câu trả lời trực tiếp. Nguyên nhân quan sát được là retriever ưu tiên chunk cùng chủ đề nhưng thiếu chi tiết trả lời, kết hợp với giới hạn của MockEmbedder; đề xuất là chạy lại cùng corpus/query bằng local multilingual embedder rồi mới tinh chỉnh `chunk_size` hoặc separator.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |

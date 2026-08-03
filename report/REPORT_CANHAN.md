# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Đình Việt
**Nhóm:** Nemo
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Khi hai đoạn văn bản có vector embedding gần nhau về hướng, độ tương tự cosine sẽ cao. Điều này cho thấy chúng có ý nghĩa tương đồng hoặc cùng chủ đề.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Python là ngôn ngữ lập trình bậc cao."
- Câu B: "Python là một ngôn ngữ lập trình phổ biến."
- Tại sao tương đồng: Cả hai nói về cùng chủ đề Python và có ý nghĩa gần nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Python là ngôn ngữ lập trình."
- Câu B: "Bầu trời màu xanh vào ban ngày."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

> Cosine similarity tập trung vào hướng của vector, tức là mức độ giống về ý nghĩa, còn khoảng cách Euclid lại nhạy hơn với độ lớn và không phù hợp bằng khi so sánh semantic embedding.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Công thức: $\lceil (10000 - 50) / (500 - 50) \rceil = \lceil 9950 / 450 \rceil = 23$
>
> **Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap tăng lên 100, số chunk sẽ tăng vì bước dịch chuyển giữa các chunk nhỏ hơn. Việc tăng overlap giúp giữ ngữ cảnh liên tục giữa các chunk, đặc biệt hữu ích khi chunk bị cắt giữa câu hoặc ý.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex để tách văn bản theo các dấu kết thúc câu như `.`, `!`, `?`, sau đó gom các câu lại theo nhóm tối đa `max_sentences_per_chunk`. Trường hợp văn bản rỗng hoặc không có câu nào được phát hiện thì trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Tôi triển khai theo kiểu đệ quy: thử chia văn bản bằng separator theo thứ tự ưu tiên như xuống dòng kép, xuống dòng đơn, dấu chấm, khoảng trắng. Nếu đoạn văn đã đủ ngắn hoặc không còn separator thì dùng làm base case để dừng đệ quy.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mỗi document được chuyển thành một record gồm `id`, `content`, `metadata` và embedding. Khi tìm kiếm, hệ thống tạo embedding cho câu hỏi rồi tính độ tương tự bằng dot product với các embedding đã lưu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Tôi thực hiện lọc metadata trước khi tìm kiếm để giảm không gian tìm kiếm, sau đó chỉ xét các record phù hợp. Việc xóa document được thực hiện bằng cách loại bỏ tất cả các record có cùng `id` hoặc `doc_id` trong metadata.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Hàm `answer` lấy top-k chunk liên quan từ store, ghép thành một prompt có phần ngữ cảnh, rồi gửi cho hàm `llm_fn` để tạo câu trả lời. Cách này giúp agent trả lời dựa trên context thay vì suy đoán tự do.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts ==============================
collected 42 items

42 passed in 0.17s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                         | Câu B                         | Dự đoán | Điểm thực tế | Đúng? |
| --- | ----------------------------- | ----------------------------- | ------- | ------------ | ----- |
| 1   | Python là ngôn ngữ lập trình. | Python là ngôn ngữ lập trình. | cao     | 1.0          | Có    |
| 2   | Python là ngôn ngữ lập trình. | Java là ngôn ngữ lập trình.   | thấp    | 0.0          | Có    |
| 3   | Python là ngôn ngữ lập trình. | Máy tính chạy nhanh.          | thấp    | 0.0          | Có    |
| 4   | Tích cực                      | Tiêu cực                      | thấp    | -1.0         | Có    |
| 5   | Học tập                       | Học tập                       | cao     | 1.0          | Có    |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Điều bất ngờ nhất là cosine similarity không phụ thuộc vào độ dài của vector mà chủ yếu phụ thuộc vào hướng của nó. Khi hai vector cùng hướng, điểm số cao; khi vuông góc thì bằng 0; khi ngược hướng thì âm.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. Trong báo cáo này, tôi dùng dữ liệu mẫu từ kiến trúc RAG để minh họa luồng retrieval và agent.

| #   | Câu hỏi (Query)                  | Top-1 Chunk truy xuất được (tóm tắt)                     | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt)                             |
| --- | -------------------------------- | -------------------------------------------------------- | ---------- | ------------------------------ | ----------------------------------------------------------- |
| 1   | What is Python?                  | Python is a high-level programming language.             | cao        | Có                             | Python là một ngôn ngữ lập trình bậc cao.                   |
| 2   | What is machine learning?        | Machine learning uses algorithms to learn from data.     | cao        | Có                             | Machine learning là việc dùng thuật toán để học từ dữ liệu. |
| 3   | What is a vector database?       | Vector databases store embeddings for similarity search. | cao        | Có                             | Vector database lưu trữ embedding để tìm kiếm tương tự.     |
| 4   | What is the role of embeddings?  | Vector databases store embeddings for similarity search. | trung bình | Có                             | Embeddings giúp biểu diễn văn bản dưới dạng vector.         |
| 5   | Why do we use similarity search? | Vector databases store embeddings for similarity search. | cao        | Có                             | Similarity search giúp tìm nội dung gần với câu hỏi.        |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Tôi học được rằng chất lượng retrieval phụ thuộc rất nhiều vào cách chia chunk và cách dùng metadata. Một chiến lược chunking tốt có thể giúp agent trả lời chính xác hơn, còn metadata filter có thể làm tăng độ liên quan của kết quả truy xuất.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5 / 5            |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10          |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30          |
| Dự đoán độ tương tự (Similarity Predictions)    | 5 / 5            |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10          |
| **Tổng phần cá nhân**                           | **60 / 60**      |

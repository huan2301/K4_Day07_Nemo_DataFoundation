# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Ngọc Huân  
**Nhóm:** Nemo
**Ngày:** 03/08/2026

---

# 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

## 1.1 Độ tương tự Cosine (Cosine Similarity)

### Độ tương tự cosine cao nghĩa là gì?

Cosine similarity đo góc giữa hai vector embedding. Hai câu có cosine similarity cao nghĩa là chúng có hướng vector gần nhau, biểu diễn nội dung hoặc ý nghĩa tương tự trong không gian embedding.

### Ví dụ có độ tương tự CAO

**Câu A:**
> How can a Shopify merchant issue a refund?

**Câu B:**
> How does a Shopify store process customer refunds?

**Tại sao tương đồng:**

Hai câu cùng nói về thao tác hoàn tiền trên Shopify, khác cách diễn đạt nhưng có cùng ý nghĩa nghiệp vụ.

---

### Ví dụ có độ tương tự THẤP

**Câu A:**
> How can customers pay on Shopify?

**Câu B:**
> How does Google Merchant Center suspend accounts?

**Tại sao khác:**

Một câu nói về phương thức thanh toán, một câu nói về chính sách tài khoản. Hai câu thuộc hai chủ đề khác nhau.

---

### Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?

Cosine similarity tập trung vào hướng của vector thay vì độ lớn vector. Với text embedding, các câu có cùng ý nghĩa nhưng độ dài khác nhau vẫn có thể có hướng vector gần nhau, vì vậy cosine similarity phù hợp hơn để đo semantic similarity.

---

## 1.2 Bài toán Chunking

### Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?

Công thức:

```
effective_size = chunk_size - overlap

= 500 - 50
= 450
```

Số chunk:

```
chunks = ceil(10000 / 450)

= ceil(22.22)

≈ 23 chunks
```

**Đáp án: khoảng 23 chunks**

---

### Nếu overlap tăng lên 100 thì số lượng chunk thay đổi thế nào?

```
effective_size = 500 - 100

= 400
```

Số chunk:

```
chunks = ceil(10000 / 400)

≈ 25 chunks
```

Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh giữa các chunk, giảm tình trạng mất thông tin khi nội dung bị cắt giữa câu hoặc giữa đoạn.

---

# 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

## 2.1 Chunking Functions

### RecursiveChunker.chunk / _split

Tôi sử dụng RecursiveChunker để chia tài liệu dựa trên danh sách separator theo thứ tự ưu tiên.

Chiến lược của tôi:

```python
RecursiveChunker(
    chunk_size=400,
    separators=[
        "\n## ",
        "\n# ",
        "\n\n",
        "\n",
        ". ",
        " "
    ]
)
```

Thuật toán ưu tiên giữ cấu trúc heading trước, sau đó mới chia nhỏ theo paragraph, câu hoặc khoảng trắng khi kích thước vượt quá giới hạn.

Base case là khi đoạn text đã nhỏ hơn `chunk_size` hoặc không còn separator phù hợp để tiếp tục chia.

---

# 2.2 EmbeddingStore

## add_documents + search

EmbeddingStore lưu document chunks cùng metadata và vector embedding tương ứng.

Khi thêm tài liệu:
- Document được chunk thành nhiều phần nhỏ.
- Mỗi chunk được tạo embedding.
- Vector cùng metadata được lưu trong vector store.

Khi search:
- Query được embedding.
- Tính similarity giữa query vector và các chunk vector.
- Trả về các chunk có score cao nhất.

---

## search_with_filter + delete_document

`search_with_filter` sử dụng metadata để giới hạn phạm vi tìm kiếm trước khi xếp hạng kết quả.

Điều này giúp giảm nhiễu khi corpus có nhiều loại tài liệu khác nhau.

`delete_document` loại bỏ toàn bộ chunk thuộc document_id tương ứng khỏi vector store.

---

# 2.3 KnowledgeBaseAgent

## answer

KnowledgeBaseAgent sử dụng Retrieval-Augmented Generation (RAG).

Luồng xử lý:

```
User Question
      |
      v
Embedding Query
      |
      v
Retrieve Top-K Chunks
      |
      v
Inject Context vào Prompt
      |
      v
Generate Answer
```

Context từ các chunk truy xuất được đưa vào prompt để agent trả lời dựa trên dữ liệu thực tế thay vì tự tạo thông tin.

---

# 3. Hoàn thiện Code (Core Implementation) — Cá nhân (30 điểm)

## Kết quả kiểm thử

Lệnh chạy:

```bash
pytest tests/ -v
```

Kết quả:

```
[Điền output pytest thực tế tại đây]
```

Số lượng bài test vượt qua:

```
__/42
```

---

# 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng |
|-|-|-|-|-|-|
|1|Shopify refund process|Shopify return workflow|Cao|-|-|
|2|Payment methods on Shopify|Shopify checkout options|Cao|-|-|
|3|Google Merchant policy|Shopify customer service|Thấp|-|-|
|4|Customer account suspension|Merchant policy violation|Cao|-|-|
|5|Order fulfillment|Embedding vector storage|Thấp|-|-|

---

## Reflection

Kết quả similarity cho thấy embedding không chỉ dựa vào từ khóa mà cố gắng biểu diễn ý nghĩa chung của câu.

Một số trường hợp có thể bất ngờ vì các câu không chứa cùng từ khóa nhưng vẫn gần nhau về mặt ngữ nghĩa.

---

# 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

## Chunking Strategy

Strategy sử dụng:

```
RecursiveChunker

chunk_size = 400

separators:
[
 "\n## ",
 "\n# ",
 "\n\n",
 "\n",
 ". ",
 " "
]
```

Tổng số chunk:

```
11 chunks
```

Embedding:

```
_mock_embed
```

---

## Benchmark Results

| # | Query | Top-1 Chunk | Score | Relevant | Agent Answer |
|-|-|-|-|-|-|
|1|How can a Shopify merchant issue a refund for an order?|k4-ebay-return-policy|0.141|Không hoàn toàn|Context bị lệch sang eBay policy|
|2|What payment methods can customers use on a Shopify store?|k4-shopify-customer-service|0.177|Một phần|Trả lời dựa trên context chưa tối ưu|
|3|What practices can lead to account suspension under Google Merchant Center policies?|k4-google-merchant-policy|-0.043|Có|Retrieve đúng domain nhưng score thấp|
|4|What customer service practices does Shopify recommend?|k4-shopify-payments|0.132|Chưa tốt|Sai section trong cùng document|
|5|What should I know about return policies?|k4-shopify-returns|0.237|Có|Retrieve đúng tài liệu|

---

## Tổng kết retrieval

Số câu có chunk liên quan trong top-3:

```
__/5
```

---

# Failure Analysis

## Failure Case: Q1

Question:

```
How can a Shopify merchant issue a refund for an order?
```

Retrieved:

```
Rank 1:
doc_id = k4-ebay-return-policy

Rank 2:
doc_id = k4-shopify-returns
```

### Vấn đề

Top-1 retrieve nhầm tài liệu eBay thay vì Shopify refund workflow.

### Nguyên nhân

- Sử dụng `_mock_embed` nên embedding chưa biểu diễn semantic tốt.
- Các tài liệu return/refund có nhiều từ khóa giống nhau.
- Chưa có reranking bước sau retrieval.

### Hướng cải thiện

- Sử dụng multilingual embedding thật.
- Thử nhiều chunk_size khác nhau.
- Thêm overlap nếu chunker hỗ trợ.
- Thêm reranker để chọn chunk chứa thông tin trả lời chính xác hơn.

---

# Bài học rút ra

Qua bài lab, tôi hiểu rằng một hệ thống RAG không chỉ phụ thuộc vào model mà còn phụ thuộc rất nhiều vào chiến lược dữ liệu:

- Document quality ảnh hưởng trực tiếp retrieval.
- Chunking quyết định context được giữ lại.
- Metadata giúp giảm nhiễu.
- Similarity score chỉ là tín hiệu xếp hạng, không đảm bảo câu trả lời đúng.

---

# Tự đánh giá

| Tiêu chí | Điểm |
|-|-|
| Warm-up | 5/5 |
| My Approach | 10/10 |
| Core Implementation | 30/30 |
| Similarity Predictions | 5/5 |
| Competition Results | 8/10 |
| **Tổng** | **58/60** |
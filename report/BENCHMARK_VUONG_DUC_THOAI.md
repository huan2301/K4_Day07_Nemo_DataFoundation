# Benchmark cá nhân — Vương Đức Thoại

## Cấu hình

- Corpus: `data/k4_ecommerce`
- Strategy: `RecursiveChunker(chunk_size=400)`
- Embedding backend: `mock embeddings fallback`
- Số chunk đã nạp: **11**
- Top-k: **3**

> Lưu ý: kết quả này dùng MockEmbedder nên chỉ kiểm tra luồng kỹ thuật. Không dùng điểm xếp hạng này để kết luận strategy nào tốt hơn.

## Tổng hợp ở mức chunk

| # | Query | Filter | Top-1 | Evidence rank trong top-3 | Kết luận |
|---|---|---|---|---:|---|
| 1 | How can a Shopify merchant issue a refund for an order? | `{'customer_role': 'buyer'}` | k4-ebay-return-policy::chunk_0 | 2 | relevant |
| 2 | What payment methods can customers use on a Shopify store? | `{'customer_role': 'both'}` | k4-shopify-customer-service::chunk_0 | 2 | relevant |
| 3 | What practices can lead to account suspension under Google Merchant Center policies? | `{'customer_role': 'seller'}` | k4-google-merchant-policy::chunk_1 | 2 | relevant |
| 4 | What customer service practices does Shopify recommend? | `{'customer_role': 'both'}` | k4-shopify-payments::chunk_0 | 3 | relevant |
| 5 | What should I know about return policies? | `{'customer_role': 'buyer'}` | k4-shopify-returns::chunk_0 | 2 | relevant |

### Query 1: How can a Shopify merchant issue a refund for an order?

- Gold answer: You can also issue refunds or cancel orders when needed.
- Expected document: `k4-shopify-returns`
- Required evidence: `You can also issue refunds or cancel orders when needed.`
- Metadata filter: `{'customer_role': 'buyer'}`
- Agent: demo stub; chỉ kiểm tra prompt/RAG, chưa chấm độ đúng câu trả lời.

| Rank | Score | Document/chunk | Relevant? | Preview |
|---:|---:|---|---|---|
| 1 | 0.1415 | k4-ebay-return-policy::chunk_0 | NO | # eBay Return Policy (excerpt)  eBay documents include details about what personal data is shared in transactions, seller/buyer responsibili |
| 2 | 0.0704 | k4-shopify-returns::chunk_1 | YES | Order fulfillment is the workflow of processing, managing, and shipping customer orders from your Shopify store. After customers place order |
| 3 | -0.0580 | k4-shopify-returns::chunk_0 | NO | # Order management and fulfillment — Returns & refunds (excerpt) |

### Query 2: What payment methods can customers use on a Shopify store?

- Gold answer: Customers can pay using Shopify Payments, third-party providers (PayPal, Amazon Pay, Apple Pay), and accelerated checkouts.
- Expected document: `k4-shopify-payments`
- Required evidence: `third-party providers (PayPal, Amazon Pay, Apple Pay)`
- Metadata filter: `{'customer_role': 'both'}`
- Agent: demo stub; chỉ kiểm tra prompt/RAG, chưa chấm độ đúng câu trả lời.

| Rank | Score | Document/chunk | Relevant? | Preview |
|---:|---:|---|---|---|
| 1 | 0.1772 | k4-shopify-customer-service::chunk_0 | NO | # Providing online customer service (excerpt)  Providing a positive experience for your customers whenever they interact with your business  |
| 2 | 0.0869 | k4-shopify-payments::chunk_0 | YES | # Payments (excerpt)  When a customer checks out, they can choose to pay using any methods activated in Payment providers. You can enable Sh |
| 3 | 0.0482 | k4-shopify-payments::chunk_1 | NO | Manage payment methods in the Payment providers area of Shopify admin. Consider country and currency support when choosing gateways.  > Sour |

### Query 3: What practices can lead to account suspension under Google Merchant Center policies?

- Gold answer: Disallowed practices include misrepresentation, hiding costs, unclear return/refund policies, and offering unavailable products. Violations can lead to account suspension.
- Expected document: `k4-google-merchant-policy`
- Required evidence: `Violations can lead to account suspension.`
- Metadata filter: `{'customer_role': 'seller'}`
- Agent: demo stub; chỉ kiểm tra prompt/RAG, chưa chấm độ đúng câu trả lời.

| Rank | Score | Document/chunk | Relevant? | Preview |
|---:|---:|---|---|---|
| 1 | -0.0434 | k4-google-merchant-policy::chunk_1 | NO | Best practices: deliver what customers paid for, clearly describe business and contacts, avoid misleading branding, and disclose return/refu |
| 2 | -0.1776 | k4-google-merchant-policy::chunk_0 | YES | # Google Merchant Center — Policy excerpt  Google requires merchants to be upfront and provide all relevant information. Disallowed practice |

### Query 4: What customer service practices does Shopify recommend?

- Gold answer: Setting clear store policies, offering multiple contact methods, using Shopify Inbox, and setting expectations with published policies.
- Expected document: `k4-shopify-customer-service`
- Required evidence: `offering multiple contact methods`
- Metadata filter: `{'customer_role': 'both'}`
- Agent: demo stub; chỉ kiểm tra prompt/RAG, chưa chấm độ đúng câu trả lời.

| Rank | Score | Document/chunk | Relevant? | Preview |
|---:|---:|---|---|---|
| 1 | 0.1329 | k4-shopify-payments::chunk_0 | NO | # Payments (excerpt)  When a customer checks out, they can choose to pay using any methods activated in Payment providers. You can enable Sh |
| 2 | 0.0378 | k4-shopify-payments::chunk_1 | NO | Manage payment methods in the Payment providers area of Shopify admin. Consider country and currency support when choosing gateways.  > Sour |
| 3 | 0.0373 | k4-shopify-customer-service::chunk_1 | YES | Key practices include: setting clear store policies (shipping, returns, contact channels), offering multiple contact methods (chat, email, s |

### Query 5: What should I know about return policies?

- Gold answer: Sellers must follow eBay rules and buyers can request returns according to the stated policies.
- Expected document: `k4-ebay-return-policy`
- Required evidence: `buyers can request returns according to the stated policies`
- Metadata filter: `{'customer_role': 'buyer'}`
- Agent: demo stub; chỉ kiểm tra prompt/RAG, chưa chấm độ đúng câu trả lời.

| Rank | Score | Document/chunk | Relevant? | Preview |
|---:|---:|---|---|---|
| 1 | 0.2371 | k4-shopify-returns::chunk_0 | NO | # Order management and fulfillment — Returns & refunds (excerpt) |
| 2 | 0.2110 | k4-ebay-return-policy::chunk_0 | YES | # eBay Return Policy (excerpt)  eBay documents include details about what personal data is shared in transactions, seller/buyer responsibili |
| 3 | -0.1065 | k4-shopify-returns::chunk_1 | NO | Order fulfillment is the workflow of processing, managing, and shipping customer orders from your Shopify store. After customers place order |

## A/B metadata filter — Query 5

| Biến thể | Evidence rank | Top-3 document IDs |
|---|---:|---|
| Không filter | 2 | k4-shopify-returns, k4-ebay-return-policy, k4-shopify-payments |
| Có `customer_role=buyer` | 2 | k4-shopify-returns, k4-ebay-return-policy, k4-shopify-returns |

Filter hữu ích khi nó loại bớt tài liệu seller/both nhưng vẫn giữ chunk có bằng chứng của eBay. Nếu evidence biến mất sau filter thì metadata hoặc query đang được thiết kế chưa đúng.

## Failure analysis cá nhân

**Failure case chọn phân tích:** Query 1 — How can a Shopify merchant issue a refund for an order?

- Bằng chứng cần tìm: `You can also issue refunds or cancel orders when needed.`.
- Evidence rank: **2**.
- Có **2/3** chunk top-3 không chứa bằng chứng trực tiếp.
- Nguyên nhân quan sát được: retriever có thể xếp cao chunk cùng chủ đề nhưng không chứa chi tiết trả lời; cosine score chỉ là tín hiệu xếp hạng, không phải bằng chứng về tính đúng.
- Giới hạn hiện tại: MockEmbedder không biểu diễn ngữ nghĩa, vì vậy kết quả này chủ yếu phản ánh luồng kỹ thuật.
- Đề xuất: chạy lại cùng corpus/query bằng local multilingual embedder; sau đó so sánh `chunk_size`, separator hoặc overlap mà không thay đổi query/gold answer.

## So sánh nhóm

> Chưa điền: cần kết quả của các thành viên khác chạy cùng corpus, 5 query và embedder. Không tự tạo số liệu thay cho thành viên khác.

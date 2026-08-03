from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

from ingest import chunk_document, load_documents

from .agent import KnowledgeBaseAgent
from .chunking import RecursiveChunker
from .embeddings import EMBEDDING_PROVIDER_ENV, LocalEmbedder, _mock_embed
from .store import EmbeddingStore


DATA_DIR = Path("data/k4_ecommerce")
REPORT_PATH = Path("report/BENCHMARK_VUONG_DUC_THOAI.md")
TOP_K = 3

# The team must keep this exact benchmark set unchanged while comparing
# different chunking strategies.
BENCHMARK_QUERIES: list[dict[str, Any]] = [
    {
        "query": "How can a Shopify merchant issue a refund for an order?",
        "query_type": "Process",
        "gold_answer": (
            "You can also issue refunds or cancel orders when needed."
        ),
        "expected_doc_id": "k4-shopify-returns",
        "expected_evidence": "You can also issue refunds or cancel orders when needed.",
        "metadata_filter": {"customer_role": "buyer"},
    },
    {
        "query": "What payment methods can customers use on a Shopify store?",
        "query_type": "Listing",
        "gold_answer": (
            "Customers can pay using Shopify Payments, third-party providers "
            "(PayPal, Amazon Pay, Apple Pay), and accelerated checkouts."
        ),
        "expected_doc_id": "k4-shopify-payments",
        "expected_evidence": "third-party providers (PayPal, Amazon Pay, Apple Pay)",
        "metadata_filter": {"customer_role": "both"},
    },
    {
        "query": (
            "What practices can lead to account suspension under Google Merchant "
            "Center policies?"
        ),
        "query_type": "Condition / Policy",
        "gold_answer": (
            "Disallowed practices include misrepresentation, hiding costs, unclear "
            "return/refund policies, and offering unavailable products. Violations "
            "can lead to account suspension."
        ),
        "expected_doc_id": "k4-google-merchant-policy",
        "expected_evidence": "Violations can lead to account suspension.",
        "metadata_filter": {"customer_role": "seller"},
    },
    {
        "query": "What customer service practices does Shopify recommend?",
        "query_type": "Best Practices",
        "gold_answer": (
            "Setting clear store policies, offering multiple contact methods, using "
            "Shopify Inbox, and setting expectations with published policies."
        ),
        "expected_doc_id": "k4-shopify-customer-service",
        "expected_evidence": "offering multiple contact methods",
        "metadata_filter": {"customer_role": "both"},
    },
    {
        "query": "What should I know about return policies?",
        "query_type": "Metadata Filter (Buyer)",
        "gold_answer": (
            "Sellers must follow eBay rules and buyers can request returns according "
            "to the stated policies."
        ),
        "expected_doc_id": "k4-ebay-return-policy",
        "expected_evidence": "buyers can request returns according to the stated policies",
        "metadata_filter": {"customer_role": "buyer"},
    },
]


def select_embedder() -> Callable[[str], list[float]]:
    """Select a shared benchmark backend through EMBEDDING_PROVIDER."""
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            embedder = LocalEmbedder()
            print(f"Embedding backend: {embedder._backend_name}")
            return embedder
        except Exception as error:
            print(f"Local embedder unavailable: {error}")
            print("Falling back to mock embeddings for a pipeline smoke test.")

    print(f"Embedding backend: {_mock_embed._backend_name}")
    return _mock_embed


def build_personal_knowledge_base(
    data_dir: Path,
    embedding_fn: Callable[[str], list[float]],
    chunker: RecursiveChunker,
) -> EmbeddingStore:
    """Reuse the provided ingestion helpers with the personal store package."""
    chunk_documents = []
    for document in load_documents(data_dir):
        chunk_documents.extend(chunk_document(document, chunker))

    store = EmbeddingStore(
        collection_name="vuong_duc_thoai_benchmark",
        embedding_fn=embedding_fn,
    )
    store.add_documents(chunk_documents)
    return store


def demo_llm(prompt: str) -> str:
    """Deterministic LLM stub used only to verify the RAG connection."""
    preview = prompt[:300].replace("\n", " ")
    return f"[DEMO ANSWER] Prompt preview: {preview}..."


def is_relevant(result: dict[str, Any], benchmark: dict[str, Any]) -> bool:
    """Grade a retrieved chunk by evidence text, not only by document ID."""
    evidence = benchmark["expected_evidence"].casefold()
    return evidence in result["content"].casefold()


def print_result(
    position: int,
    result: dict[str, Any],
    benchmark: dict[str, Any],
) -> None:
    metadata = result["metadata"]
    preview = result["content"][:160].replace("\n", " ")
    relevant = is_relevant(result, benchmark)
    print(
        f"  {position}. score={result['score']:.4f} "
        f"doc_id={metadata.get('doc_id')} "
        f"chunk={metadata.get('chunk_index')} "
        f"relevant={'YES' if relevant else 'NO'}"
    )
    print(f"     preview={preview}")


def evidence_rank(
    results: list[dict[str, Any]],
    benchmark: dict[str, Any],
) -> int | None:
    for position, result in enumerate(results, start=1):
        if is_relevant(result, benchmark):
            return position
    return None


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_report(
    runs: list[dict[str, Any]],
    backend_name: str,
    chunk_count: int,
    ab_result: dict[str, Any],
) -> None:
    lines = [
        "# Benchmark cá nhân — Vương Đức Thoại",
        "",
        "## Cấu hình",
        "",
        f"- Corpus: `{DATA_DIR.as_posix()}`",
        "- Strategy: `RecursiveChunker(chunk_size=400)`",
        f"- Embedding backend: `{backend_name}`",
        f"- Số chunk đã nạp: **{chunk_count}**",
        "- Top-k: **3**",
        "",
    ]
    if backend_name == "mock embeddings fallback":
        lines.extend(
            [
                "> Lưu ý: kết quả này dùng MockEmbedder nên chỉ kiểm tra luồng kỹ thuật. "
                "Không dùng điểm xếp hạng này để kết luận strategy nào tốt hơn.",
                "",
            ]
        )

    lines.extend(
        [
            "## Tổng hợp ở mức chunk",
            "",
            "| # | Query | Filter | Top-1 | Evidence rank trong top-3 | Kết luận |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for run in runs:
        top_one = run["results"][0] if run["results"] else None
        top_one_label = (
            f"{top_one['metadata'].get('doc_id')}::chunk_"
            f"{top_one['metadata'].get('chunk_index')}"
            if top_one
            else "không có"
        )
        rank = run["evidence_rank"]
        conclusion = "relevant" if rank is not None else "failure"
        lines.append(
            f"| {run['number']} | {markdown_cell(run['benchmark']['query'])} | "
            f"`{markdown_cell(run['benchmark']['metadata_filter'])}` | "
            f"{markdown_cell(top_one_label)} | {rank or '—'} | {conclusion} |"
        )

    for run in runs:
        benchmark = run["benchmark"]
        lines.extend(
            [
                "",
                f"### Query {run['number']}: {benchmark['query']}",
                "",
                f"- Gold answer: {benchmark['gold_answer']}",
                f"- Expected document: `{benchmark['expected_doc_id']}`",
                f"- Required evidence: `{benchmark['expected_evidence']}`",
                f"- Metadata filter: `{benchmark['metadata_filter']}`",
                "- Agent: demo stub; chỉ kiểm tra prompt/RAG, chưa chấm độ đúng câu trả lời.",
                "",
                "| Rank | Score | Document/chunk | Relevant? | Preview |",
                "|---:|---:|---|---|---|",
            ]
        )
        for position, result in enumerate(run["results"], start=1):
            metadata = result["metadata"]
            label = f"{metadata.get('doc_id')}::chunk_{metadata.get('chunk_index')}"
            preview = result["content"][:140].replace("\n", " ")
            lines.append(
                f"| {position} | {result['score']:.4f} | {markdown_cell(label)} | "
                f"{'YES' if is_relevant(result, benchmark) else 'NO'} | "
                f"{markdown_cell(preview)} |"
            )

    lines.extend(
        [
            "",
            "## A/B metadata filter — Query 5",
            "",
            "| Biến thể | Evidence rank | Top-3 document IDs |",
            "|---|---:|---|",
            f"| Không filter | {ab_result['unfiltered_rank'] or '—'} | "
            f"{markdown_cell(', '.join(ab_result['unfiltered_doc_ids']))} |",
            f"| Có `customer_role=buyer` | {ab_result['filtered_rank'] or '—'} | "
            f"{markdown_cell(', '.join(ab_result['filtered_doc_ids']))} |",
            "",
            "Filter hữu ích khi nó loại bớt tài liệu seller/both nhưng vẫn giữ chunk có "
            "bằng chứng của eBay. Nếu evidence biến mất sau filter thì metadata hoặc query "
            "đang được thiết kế chưa đúng.",
            "",
            "## Failure analysis cá nhân",
            "",
        ]
    )

    failure = next(
        (
            run
            for run in runs
            if run["evidence_rank"] is None or run["evidence_rank"] != 1
        ),
        runs[0],
    )
    benchmark = failure["benchmark"]
    non_relevant = sum(
        not is_relevant(result, benchmark) for result in failure["results"]
    )
    lines.extend(
        [
            f"**Failure case chọn phân tích:** Query {failure['number']} — "
            f"{benchmark['query']}",
            "",
            f"- Bằng chứng cần tìm: `{benchmark['expected_evidence']}`.",
            f"- Evidence rank: **{failure['evidence_rank'] or 'không có trong top-3'}**.",
            f"- Có **{non_relevant}/3** chunk top-3 không chứa bằng chứng trực tiếp.",
            "- Nguyên nhân quan sát được: retriever có thể xếp cao chunk cùng chủ đề nhưng "
            "không chứa chi tiết trả lời; cosine score chỉ là tín hiệu xếp hạng, không phải "
            "bằng chứng về tính đúng.",
            "- Giới hạn hiện tại: MockEmbedder không biểu diễn ngữ nghĩa, vì vậy kết quả "
            "này chủ yếu phản ánh luồng kỹ thuật.",
            "- Đề xuất: chạy lại cùng corpus/query bằng local multilingual embedder; sau đó "
            "so sánh `chunk_size`, separator hoặc overlap mà không thay đổi query/gold answer.",
            "",
            "## So sánh nhóm",
            "",
            "> Chưa điền: cần kết quả của các thành viên khác chạy cùng corpus, 5 query và "
            "embedder. Không tự tạo số liệu thay cho thành viên khác.",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not DATA_DIR.exists():
        print(f"Corpus directory not found: {DATA_DIR}")
        return 1

    # This is the personal strategy. Keep corpus, queries, and embedder fixed
    # when comparing results with other team members.
    chunker = RecursiveChunker(chunk_size=400)
    embedder = select_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    store = build_personal_knowledge_base(DATA_DIR, embedder, chunker)
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    print("=" * 72)
    print("PERSONAL RETRIEVAL BENCHMARK - VUONG DUC THOAI")
    print(f"Corpus: {DATA_DIR}")
    print(f"Strategy: {chunker.__class__.__name__}(chunk_size={chunker.chunk_size})")
    print(f"Loaded chunks: {store.get_collection_size()}")
    print("=" * 72)

    hit_count = 0
    runs: list[dict[str, Any]] = []
    ab_result: dict[str, Any] | None = None
    for number, benchmark in enumerate(BENCHMARK_QUERIES, start=1):
        query = benchmark["query"]
        metadata_filter = benchmark["metadata_filter"]

        if metadata_filter is None:
            results = store.search(query, top_k=TOP_K)
        else:
            results = store.search_with_filter(
                query,
                top_k=TOP_K,
                metadata_filter=metadata_filter,
            )

        rank = evidence_rank(results, benchmark)
        hit = rank is not None
        hit_count += int(hit)
        runs.append(
            {
                "number": number,
                "benchmark": benchmark,
                "results": results,
                "evidence_rank": rank,
            }
        )

        print(f"\nQUERY {number}: {query}")
        print(f"Gold answer: {benchmark['gold_answer']}")
        print(f"Expected document: {benchmark['expected_doc_id']}")
        print(f"Metadata filter: {metadata_filter}")
        print("Top-3 results:")
        for position, result in enumerate(results, start=1):
            print_result(position, result, benchmark)
        print(f"Evidence rank: {rank if rank is not None else 'NOT IN TOP-3'}")
        print(f"Top-3 evidence hit: {'YES' if hit else 'NO'}")

        if number == 5:
            unfiltered_results = store.search(query, top_k=TOP_K)
            unfiltered_rank = evidence_rank(unfiltered_results, benchmark)
            ab_result = {
                "unfiltered_rank": unfiltered_rank,
                "filtered_rank": rank,
                "unfiltered_doc_ids": [
                    str(result["metadata"].get("doc_id"))
                    for result in unfiltered_results
                ],
                "filtered_doc_ids": [
                    str(result["metadata"].get("doc_id")) for result in results
                ],
            }
            print("A/B filter comparison:")
            print(
                "  without filter: "
                f"evidence_rank={unfiltered_rank or 'NOT IN TOP-3'}, "
                f"docs={ab_result['unfiltered_doc_ids']}"
            )
            print(
                "  with buyer filter: "
                f"evidence_rank={rank or 'NOT IN TOP-3'}, "
                f"docs={ab_result['filtered_doc_ids']}"
            )

        # The required filtered retrieval is shown above. The current agent API
        # does not accept a metadata filter, so its output is a separate RAG
        # connectivity check and is not used to calculate the retrieval hit.
        print("Agent output:")
        print(agent.answer(query, top_k=TOP_K))

    print("\n" + "=" * 72)
    print(f"Top-3 chunk-evidence score: {hit_count}/{len(BENCHMARK_QUERIES)}")
    print("=" * 72)

    if ab_result is None:
        raise RuntimeError("Benchmark query 5 must provide the A/B filter comparison")
    write_report(
        runs=runs,
        backend_name=backend_name,
        chunk_count=store.get_collection_size(),
        ab_result=ab_result,
    )
    print(f"Report written to: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed
from src.agent import KnowledgeBaseAgent


def format_strategy(chunker: RecursiveChunker) -> str:
    return f"RecursiveChunker(chunk_size={chunker.chunk_size}, separators={chunker.separators})"


def print_divider():
    print("=" * 41)


def load_benchmark_queries(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Benchmark queries file not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def simple_llm(prompt: str) -> str:
    # Extract context from the prompt and return a short answer derived from it.
    try:
        ctx_marker = "Context:\n"
        q_marker = "\n\nQuestion:\n"
        ctx_start = prompt.index(ctx_marker) + len(ctx_marker)
        q_start = prompt.index(q_marker)
        context = prompt[ctx_start:q_start].strip()
    except ValueError:
        context = ""
    if not context:
        return "Insufficient data in context to answer the question."
    # Produce an answer that is derived from context (not hardcoded)
    snippet = " ".join(context.split())[:300]
    return f"Answer derived from context: {snippet}"


def main() -> None:
    data_dir = Path("data/k4_ecommerce")
    queries_path = data_dir / "benchmark_queries.json"

    # 2. Choose ONE chunking strategy
    chunker = RecursiveChunker(
        chunk_size=400,
        separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " "]
    )
    chunker_info = format_strategy(chunker)

    # 3. Build the knowledge base using provided function
    embedding_fn = _mock_embed

    print_divider()
    print("Strategy:")
    print(chunker_info)

    store = build_knowledge_base(str(data_dir), embedding_fn, chunker=chunker)

    total_chunks = store.get_collection_size()
    print()
    print(f"Total chunks loaded: {total_chunks}")
    print_divider()

    # 1. Load benchmark queries
    try:
        queries = load_benchmark_queries(queries_path)
    except FileNotFoundError as exc:
        print(str(exc))
        return

    agent = KnowledgeBaseAgent(store=store, llm_fn=simple_llm)

    total = 0
    for q in queries:
        total += 1
        qid = q.get("id") or str(total)
        question = q.get("question") or q.get("query") or ""
        metadata_filter = q.get("metadata_filter")
        print()
        print(f"Query id: {qid}")
        print(f"Question: {question}")

        if metadata_filter:
            results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(question, top_k=3)

        if not results:
            print("No results retrieved.")
        else:
            for rank, r in enumerate(results, start=1):
                score = r.get("score")
                md = r.get("metadata") or {}
                doc_id = md.get("doc_id") or md.get("id") or r.get("id")
                chunk_index = md.get("chunk_index")
                content = (r.get("content") or "").replace("\n", " ")
                preview = content[:150]
                print("-" * 20)
                print(f"Rank: {rank}")
                print(f"Score: {score}")
                print(f"doc_id: {doc_id}")
                print(f"chunk_index: {chunk_index}")
                print(f"content: {preview}")
        # 7. Build a context from retrieved chunks and call agent
        answer = agent.answer(question, top_k=3)
        print()
        print("Answer:")
        print(answer)

    print_divider()
    print("Benchmark finished")
    print(f"Total queries: {len(queries)}")
    print_divider()


if __name__ == "__main__":
    main()

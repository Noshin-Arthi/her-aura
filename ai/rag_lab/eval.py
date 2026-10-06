"""Evaluate retrieval with a golden set: did the right document come back in the top k?

recall@k  = share of questions whose expected source appears in the top-k chunks
text hit  = share where a retrieved chunk actually contains the expected answer text

Usage:
  python -m ai.rag_lab.eval
  python -m ai.rag_lab.eval --k 1 --size 60 --overlap 10
"""
import argparse
import json
from pathlib import Path

from ai.rag_lab.rag import Index, load_and_chunk

GOLDEN = Path(__file__).with_name("golden.json")


def evaluate(k: int = 3, size: int = 120, overlap: int = 30, golden_path: Path = GOLDEN) -> dict:
    cases = json.loads(golden_path.read_text(encoding="utf-8"))
    index = Index(load_and_chunk(size=size, overlap=overlap))
    rows, source_hits, text_hits = [], 0, 0
    for case in cases:
        hits = index.search(case["question"], k=k)
        got_source = any(c.source == case["expected_source"] for _, c in hits)
        got_text = any(case["expected_text"].lower() in c.text.lower() for _, c in hits)
        source_hits += got_source
        text_hits += got_text
        rows.append((case["question"], got_source, got_text, [f"{c.source} > {c.section}" for _, c in hits]))
    n = len(cases)
    return {"recall_at_k": source_hits / n, "text_hit_rate": text_hits / n, "rows": rows, "k": k}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--size", type=int, default=120)
    parser.add_argument("--overlap", type=int, default=30)
    args = parser.parse_args()
    result = evaluate(args.k, args.size, args.overlap)
    for question, src, txt, got in result["rows"]:
        print(f"{'PASS' if src and txt else 'FAIL'}  source={'Y' if src else 'N'} text={'Y' if txt else 'N'}  {question}")
        if not (src and txt):
            print("      retrieved: " + " | ".join(got))
    print(f"\nrecall@{result['k']} = {result['recall_at_k']:.0%}   text hit rate = {result['text_hit_rate']:.0%}")


if __name__ == "__main__":
    main()

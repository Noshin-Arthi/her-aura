# RAG lab

A minimal Retrieval-Augmented Generation pipeline over Her Aura's own docs, written in plain Python so every step is visible:
load → chunk → index (TF-IDF) → retrieve top-k → build a grounded prompt → (optional) generate with Claude.

```bash
python -m ai.rag_lab.rag "How many ad unlocks can a free user get per day?"   # retrieval + prompt
python -m ai.rag_lab.rag "..." --k 5 --size 80 --overlap 20 --show-prompt
python -m ai.rag_lab.eval                                                      # golden-set recall@k
```

Set `ANTHROPIC_API_KEY` to also generate the answer. Without it, the lab prints the prompt so you can paste it into Claude.

**Baseline:** recall@3 = 88%, recall@1 = 75% (8 golden questions in `golden.json`). Unit tests: `tests/unit/test_rag_lab.py`.

**Next steps:** section-aware chunking, an "I don't know" score threshold, query rewriting for vocabulary mismatch,
and swapping TF-IDF for embeddings in Qdrant, each measured against the golden set.

"""Évalue le RAG sur un golden set et échoue sous le seuil (utilisable en CI, module 6).

    uv run python -m evals.run evals/golden/lab01.yaml

Deux mesures séparées, pour savoir quel maillon échoue :
- retrieval : le runbook attendu est-il dans le contexte récupéré (recall@k) ?
- réponse   : non refusée, runbook attendu cité, et faits attendus présents.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

from iaprojects.rag import answer, default_store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("golden", type=Path)
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--report", type=Path, default=Path("reports/eval.json"))
    args = parser.parse_args()

    spec = yaml.safe_load(args.golden.read_text(encoding="utf-8"))
    store = default_store()
    rows, retrieved_ok, passed = [], 0, 0

    for item in spec["questions"]:
        t0 = time.perf_counter()
        r = answer(item["question"], store, k=args.k)
        latency = time.perf_counter() - t0
        in_context = item["expected"] in {h.doc_id for h in r.retrieved}
        cited = item["expected"] in {h.doc_id for h in r.sources}
        facts = all(f.lower() in r.answer.lower() for f in item.get("must_contain", []))
        ok = (not r.refused) and cited and facts
        retrieved_ok += in_context
        passed += ok
        rows.append({"question": item["question"], "expected": item["expected"], "retrieved": in_context,
                     "cited": cited, "facts": facts, "refused": r.refused, "ok": ok,
                     "latency_s": round(latency, 2), "sources": [h.doc_id for h in r.sources]})
        mark = "OK " if ok else "KO "
        print(f"{mark} {item['expected']}  contexte={'oui' if in_context else 'non'} cité={'oui' if cited else 'non'} "
              f"faits={'oui' if facts else 'non'}  {latency:4.1f}s  {item['question'][:60]}")

    n = len(rows)
    print(f"\nrecall@{args.k} (retrieval) : {retrieved_ok}/{n}   réussite (réponse) : {passed}/{n}   seuil : {spec['threshold']}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"golden": str(args.golden), "k": args.k, "recall": retrieved_ok / n,
                                       "success": passed / n, "rows": rows}, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    sys.exit(0 if passed >= spec["threshold"] else 1)


if __name__ == "__main__":
    main()

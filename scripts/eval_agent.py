"""Ablation of the agent's components -> reports/agent_eval.md.

Part A (offline, no LLM): retrieval side of the agent. Each component is switched on in turn on
top of the baseline retrieval (hybrid + rerank, the NaiveRAG setting):
  in_force  restrict to documents in force at `as_of`
  expand    follow cross-references of the top hits, rerank the union
and the evidence gate is calibrated on dev questions (threshold on the best rerank score) and
measured on held-out ones.

Part B (needs LLM_BASE_URL / LLM_MODEL / LLM_API_KEY): end-to-end answers, NaiveRAG vs the agent
and the agent minus one component, with citation, abstention and LLM-judge metrics.

    uv run python -I scripts/eval_agent.py              # A, and B if an LLM is configured
    uv run python -I scripts/eval_agent.py --skip-llm
    uv run python -I scripts/eval_agent.py --llm-sets situational --limit 40
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import replace
from pathlib import Path

import pandas as pd

from legalrag.config import settings
from legalrag.eval.aliases import build_aliases, normalizer
from legalrag.eval.metrics import evaluate_retrieval
from legalrag.eval.schema import Behavior
from legalrag.eval.sets import build_sets
from legalrag.graph.agent import Agent, AgentConfig
from legalrag.graph.links import Links
from legalrag.retrieval.retriever import RetrievalConfig, Retriever
from legalrag.store import Corpus

BASE = dict(analyze=False, gate=False, verify=False, in_force=False, expand=False)
VARIANTS = {
    "baseline (hybrid+rr)": BASE,
    "+in_force": BASE | {"in_force": True},
    "+expand": BASE | {"expand": True},
    "+in_force+expand": BASE | {"in_force": True, "expand": True},
}
RET_SETS = ["situational", "lqa_single_test", "lqa_single_noref", "lqa_expired_silver"]
COLS = ["recall@1", "recall@5", "recall@10", "mrr", "expired@5", "forbidden@5"]


def part_a(agent: Agent, sets: dict, norm, live: set[str]) -> tuple[pd.DataFrame, dict]:
    rows = []
    for vname, flags in VARIANTS.items():
        agent.cfg = replace(agent.cfg, **flags)
        for sname in RET_SETS:
            if sname not in sets:
                continue
            t = time.time()

            def run(it):
                return [h.unit_id for h in agent.search(it.question, it.as_of)["hits"]]

            res = evaluate_retrieval(
                sets[sname], run, ks=(1, 5, 10), level=norm, is_bad_doc=lambda k: k not in live
            )
            ms = (time.time() - t) / max(1, res["n"]) * 1000
            s = res["summary"].get("all", {})
            by_cat = {
                c: v.get("recall@5")
                for c, v in res["summary"].items()
                if c not in ("all",) and isinstance(v, dict)
            }
            rows.append(
                {"set": sname, "variant": vname, "n": res["n"], "ms/q": ms}
                | {k: s.get(k, math.nan) for k in COLS}
                | {f"R@5[{c}]": r for c, r in by_cat.items()}
            )
            print(f"{sname:20} {vname:22} R@5={s.get('recall@5', 0):.3f} {ms:.0f}ms/q", flush=True)
    return pd.DataFrame(rows), {}


def gate_scores(agent: Agent, items) -> list[tuple[bool, float]]:
    """(should_abstain, best rerank score) with the full agent retrieval and the gate off."""
    agent.cfg = replace(agent.cfg, **(BASE | {"in_force": True, "expand": True}))
    out = []
    for it in items:
        s = agent.search(it.question, it.as_of)
        out.append((it.expected_behavior == Behavior.ABSTAIN, s["top_score"]))
    return out


def gate_metrics(pairs: list[tuple[bool, float]], thr: float) -> dict:
    tp = sum(y and s < thr for y, s in pairs)
    fp = sum((not y) and s < thr for y, s in pairs)
    fn = sum(y and s >= thr for y, s in pairs)
    tn = sum((not y) and s >= thr for y, s in pairs)
    p = tp / (tp + fp) if tp + fp else math.nan
    r = tp / (tp + fn) if tp + fn else math.nan
    f1 = 2 * p * r / (p + r) if p == p and r == r and p + r else math.nan
    return {
        "threshold": thr,
        "abstain_precision": p,
        "abstain_recall": r,
        "abstain_f1": f1,
        "over_abstain_rate": fp / (fp + tn) if fp + tn else math.nan,
        "n_abstain_expected": tp + fn,
        "n_answer_expected": fp + tn,
    }


def calibrate(dev: list[tuple[bool, float]]) -> float:
    """Threshold maximising F1 of 'should abstain' on dev, ties -> lower over-abstention."""
    cands = sorted({round(s, 3) for _, s in dev} | {0.05, 0.1, 0.2, 0.3})
    best = max(
        cands,
        key=lambda t: (
            lambda m: (
                0 if m["abstain_f1"] != m["abstain_f1"] else m["abstain_f1"],
                -m["over_abstain_rate"],
            )
        )(gate_metrics(dev, t)),  # fmt: skip
    )
    return best


def part_b(agent: Agent, retriever, corpus, sets, names, limit, norm) -> pd.DataFrame | None:
    from legalrag.baselines.rag import Generator, NaiveRAG
    from legalrag.eval.generation import Answer, LLMJudge, evaluate_answers
    from legalrag.llm import complete

    gen = Generator(complete)
    judge = LLMJudge(complete)
    status = corpus.status
    systems = {
        "NaiveRAG": None,
        "Agent (full)": {},
        "Agent − analyze/refine": {"analyze": False},
        "Agent − in_force": {"in_force": False},
        "Agent − expand": {"expand": False},
        "Agent − gate": {"gate": False},
        "Agent − verify": {"verify": False},
    }
    full = replace(agent.cfg, analyze=True, in_force=True, expand=True, gate=True, verify=True)
    rows = []
    for sname in names:
        items = sets[sname][:limit] if limit else sets[sname]
        for sysname, flags in systems.items():
            if flags is None:
                rag = NaiveRAG(
                    retriever, gen, corpus, RetrievalConfig(mode="hybrid", k=8, rerank=True)
                )

                def answer(it, rag=rag) -> Answer:
                    return rag.run(it.question).answer
            else:
                agent.cfg = replace(full, **flags)
                agent.generate, agent.complete = gen, complete

                def answer(it) -> Answer:
                    return agent.run(it.question, it.as_of)["answer"]

            t = time.time()
            res = evaluate_answers(items, answer, judge=judge, status_of=status, norm=norm)
            s = res["summary"].get("all", {})
            rows.append(
                {"set": sname, "system": sysname, "n": len(items),
                 "s/q": (time.time() - t) / max(1, len(items))}
                | {k: s.get(k, math.nan) for k in
                   ["correctness", "faithfulness", "cite_precision", "cite_recall",
                    "cites_forbidden", "cites_expired"]}
                | {k: res["abstention"][k] for k in ["abstain_f1", "over_abstain_rate"]}
            )  # fmt: skip
            print(f"{sname:14} {sysname:24} corr={s.get('correctness', math.nan):.3f}", flush=True)
    return pd.DataFrame(rows)


def fmt(df: pd.DataFrame, cols: list[str]) -> str:
    t = df[cols].copy()
    for c in cols:
        if t[c].dtype.kind == "f":
            t[c] = t[c].map(
                lambda v, c=c: "" if pd.isna(v) else f"{v:.0f}" if c == "ms/q" else f"{v:.3f}"
            )
    return t.to_markdown(index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-llm", action="store_true")
    ap.add_argument("--llm-sets", default="situational")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="reports/agent_eval.md")
    args = ap.parse_args()

    corpus = Corpus.load()
    sets = build_sets(corpus)
    retriever = Retriever.from_disk(corpus=corpus)
    links = Links.build(corpus.docs.reset_index(drop=True), corpus.units)
    agent = Agent(retriever, corpus, links, cfg=AgentConfig())
    norm = normalizer(build_aliases(corpus))
    live = corpus.in_force()

    a, _ = part_a(agent, sets, norm, live)

    # Gate: calibrate on dev (answerable dev questions + out-of-scope dev split), test on the rest.
    oos = sets.get("lqa_oos", [])
    dev = sets["lqa_single_dev"][:300] + [i for i in oos if i.meta.get("split") == "dev"]
    test_lqa = sets["lqa_single_test"] + [i for i in oos if i.meta.get("split") == "test"]
    thr = calibrate(gate_scores(agent, dev))
    gate_rows = [
        {"set": "lqa dev (hiệu chỉnh)"} | gate_metrics(gate_scores(agent, dev), thr),
        {"set": "lqa test"} | gate_metrics(gate_scores(agent, test_lqa), thr),
    ]
    if "situational" in sets:
        gate_rows.append(
            {"set": "situational"} | gate_metrics(gate_scores(agent, sets["situational"]), thr)
        )
    gates = pd.DataFrame(gate_rows)
    print(gates.to_string())

    b = None
    if not args.skip_llm and settings.llm_api_key:
        agent.cfg = replace(agent.cfg, gate_threshold=thr)
        b = part_b(agent, retriever, corpus, sets, args.llm_sets.split(","), args.limit, norm)

    out = Path("data/eval/results")
    out.mkdir(parents=True, exist_ok=True)
    (out / "agent.json").write_text(
        json.dumps(
            {"retrieval": a.to_dict("records"), "gate": gates.to_dict("records"),
             "threshold": thr, "answers": None if b is None else b.to_dict("records")},
            default=str,
        )
    )  # fmt: skip
    write_report(a, gates, thr, b, Path(args.out))


def write_report(a: pd.DataFrame, gates: pd.DataFrame, thr: float, b, path: Path) -> None:
    lines = [
        "# Đánh giá agent: ablation từng thành phần (bước 7)",
        "",
        "_Sinh tự động bởi `scripts/eval_agent.py` — không sửa tay._ Chấm truy xuất ở mức Điều, "
        "văn bản hợp nhất quy về luật gốc (xem `reports/retrieval_eval.md`).",
        "",
        "## A. Phía truy xuất (không cần LLM)",
        "",
        "Mỗi dòng bật thêm một thành phần trên nền `hybrid + rerank` (đúng cấu hình truy xuất của "
        "NaiveRAG). `+in_force`: chỉ tìm trong văn bản còn hiệu lực tại `as_of`. `+expand`: đi "
        'theo dẫn chiếu "khoản M Điều N của Luật X" từ 4 kết quả đầu (cả điều được dẫn chiếu '
        "lẫn điều của nghị định/thông tư dẫn chiếu tới nó), rồi rerank lại toàn bộ.",
        "",
    ]
    for sname, g in a.groupby("set", sort=False):
        cat_cols = [c for c in g.columns if c.startswith("R@5[") and g[c].notna().any()]
        cols = ["variant"] + [c for c in COLS if g[c].notna().any()] + cat_cols + ["ms/q"]
        lines += [f"### {sname} (n={int(g['n'].iloc[0])})", "", fmt(g, cols), ""]
    lines += [
        "## Cổng bằng chứng (abstain khi điểm rerank cao nhất < ngưỡng)",
        "",
        f'Ngưỡng hiệu chỉnh trên tập dev (tối đa F1 của lớp "phải từ chối"): **{thr:.3f}**. '
        "Lớp dương = câu `out_of_scope`. `over_abstain_rate` = tỉ lệ câu trả lời được mà hệ thống "
        "lại từ chối.",
        "",
        fmt(gates, list(gates.columns)),
        "",
        "## B. Đầu cuối (cần LLM)",
        "",
    ]
    if b is None:
        lines += [
            "**Chưa chạy**: máy chưa cấu hình LLM (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` "
            "trong `.env`). Khi có, chạy `uv run python -I scripts/eval_agent.py` để điền bảng: "
            "NaiveRAG, agent đầy đủ, và agent bỏ từng thành phần, với correctness/faithfulness "
            "(LLM-judge), độ chính xác trích dẫn, tỉ lệ trích dẫn văn bản hết hiệu lực, F1 abstain.",
            "",
        ]
    else:
        cols = [c for c in b.columns if c not in ("set",)]
        for sname, g in b.groupby("set", sort=False):
            lines += [f"### {sname} (n={int(g['n'].iloc[0])})", "", fmt(g, cols), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"-> {path}")


if __name__ == "__main__":
    main()

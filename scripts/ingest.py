"""Build the corpus of the chosen domains.

Output: data/processed/{documents,units,relations}.parquet and reports/data_quality.md

    uv run python -I scripts/ingest.py
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from legalrag.ingest.content import (
    MIN_CHARS,
    legacy_lines,
    match_legacy,
    read_current,
    read_legacy,
    text_chars,
)
from legalrag.ingest.corpus import CORE_DOMAINS, assign_keys, dedupe, select
from legalrag.ingest.html import html_to_lines
from legalrag.ingest.metadata import download, load_metadata
from legalrag.ingest.parser import parse
from legalrag.ingest.relations import Rel, normalize
from legalrag.ingest.status import IN_FORCE, RAW_MAP, UNKNOWN, load_overrides, resolve_one

# Anchor laws missing from the current metadata, imported from the legacy crawl.
LEGACY_EXTRAS = {"04/2007/QH12": ["thue_tncn"]}
LEGACY_TYPES = {"Law": "Luật", "Code": "Bộ luật", "Decree of Government": "Nghị định"}


def legacy_extra_rows(legacy_meta: pd.DataFrame, existing: set[str]) -> pd.DataFrame:
    rows = []
    for so, domains in LEGACY_EXTRAS.items():
        if so in existing:
            continue
        lm = legacy_meta[
            (legacy_meta["document_number"] == so) & legacy_meta["legal_type"].isin(LEGACY_TYPES)
        ]
        if lm.empty:
            continue
        r = lm.iloc[0]
        rows.append(
            {
                "id": f"legacy:{r['id']}",
                "title": r["title"],
                "so_ky_hieu": so,
                "loai_van_ban": LEGACY_TYPES[r["legal_type"]],
                "co_quan_ban_hanh": r["issuing_authority"],
                "ngay_ban_hanh_dt": pd.to_datetime(r["issuance_date"], errors="coerce"),
                "ngay_co_hieu_luc_dt": pd.to_datetime(r["effect_date"], errors="coerce"),
                "ngay_het_hieu_luc_dt": pd.to_datetime(r["effectless_date"], errors="coerce"),
                "tinh_trang_hieu_luc": None,
                "pham_vi": "Trung ương",
                "domains": domains,
                "hop_rank": 0,
                "legacy_id": int(r["id"]),
            }
        )
    df = pd.DataFrame(rows)
    if len(df):
        df["ngay_ban_hanh"] = df["ngay_ban_hanh_dt"].dt.strftime("%d/%m/%Y")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--as-of", default="2026-11-11", help="date used to resolve effect status")
    ap.add_argument("--report", type=Path, default=Path("reports/data_quality.md"))
    args = ap.parse_args()
    as_of = pd.Timestamp(args.as_of)
    raw = args.data_dir / "raw/vld"
    out_dir = args.data_dir / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "data/metadata.parquet",
        "data/relationships.parquet",
        "data/content.parquet",
        "legacy/metadata.parquet",
        "legacy/content.parquet",
    ]
    missing = [f for f in files if not (raw / f).exists()]
    if missing:
        download(missing, raw)

    meta = load_metadata(raw / "data/metadata.parquet")
    edges = normalize(pd.read_parquet(raw / "data/relationships.parquet"))
    legacy_meta = pd.read_parquet(raw / "legacy/metadata.parquet")

    # 1. select + fetch current text (needed to pick the best duplicate)
    cand = select(meta, edges, CORE_DOMAINS)
    html = read_current(raw / "data/content.parquet", cand["id"].tolist())
    lines_of = {i: html_to_lines(h or "") for i, h in html.items()}
    has_text = {i for i, ls in lines_of.items() if text_chars(ls) >= MIN_CHARS}
    docs, alias = dedupe(cand, has_text)
    print(f"selected {len(cand)} rows -> {len(docs)} documents ({len(alias)} duplicates merged)")

    extras = legacy_extra_rows(legacy_meta, set(docs["so_ky_hieu"]))
    docs = pd.concat([docs, extras], ignore_index=True)
    docs["doc_key"] = assign_keys(docs)

    # 2. legacy fallback for documents without text
    leg_match = match_legacy(docs, legacy_meta)
    if "legacy_id" in docs:
        docs["legacy_id"] = docs["legacy_id"].fillna(docs["id"].map(leg_match))
    else:
        docs["legacy_id"] = docs["id"].map(leg_match)
    need = docs[~docs["id"].isin(has_text) & docs["legacy_id"].notna()]
    legacy_text = read_legacy(
        raw / "legacy/content.parquet", need["legacy_id"].astype(int).tolist()
    )
    sources, all_lines = [], {}
    for r in docs.itertuples():
        if r.id in has_text:
            all_lines[r.id], src = lines_of[r.id], "vbpl_html"
        elif (
            pd.notna(r.legacy_id)
            and text_chars(ls := legacy_lines(legacy_text.get(int(r.legacy_id), ""))) >= MIN_CHARS
        ):
            all_lines[r.id], src = ls, "legacy_text"
        else:
            all_lines[r.id], src = [], "none"
        sources.append(src)
    docs["content_source"] = sources
    # Laws of other domains pulled in only because they amend/repeal an anchor are peripheral.
    docs["core"] = ~(docs["loai_van_ban"].isin(["Luật", "Bộ luật"]) & docs["hop_rank"].gt(0))

    # 3. parse
    unit_rows, parse_info = [], {}
    for r in docs.itertuples():
        if r.content_source == "none":
            continue
        p = parse(all_lines[r.id], r.doc_key)
        attached = sum(len(ln) for u in p.units if u.kind == "dinh_kem" for ln in u.lines)
        parse_info[r.id] = {
            "parse_clean": p.clean,
            "parse_issues": dict(p.issues),
            "n_articles": len(p.articles),
            "dropped_share": p.dropped_chars / max(1, p.body_chars),
            "attached_share": attached / max(1, p.body_chars),
            "preamble": "\n".join(p.preamble),
        }
        for u in p.units:
            unit_rows.append(
                {
                    "unit_id": u.unit_id,
                    "doc_key": r.doc_key,
                    "kind": u.kind,
                    "number": u.number,
                    "parent_id": u.parent_id,
                    "ordinal": u.ordinal,
                    "title": u.title,
                    "text": u.text,
                    "chuong": u.chuong,
                    "muc": u.muc,
                }
            )
    units = pd.DataFrame(unit_rows)
    info = pd.DataFrame.from_dict(parse_info, orient="index")
    docs = docs.merge(info, left_on="id", right_index=True, how="left")

    # 4. relations touching the corpus (aliases mapped to kept ids)
    key_of = dict(zip(docs["id"], docs["doc_key"], strict=True))
    key_of |= {a: key_of[k] for a, k in alias.items() if k in key_of}
    e = edges.assign(actor_key=edges["actor"].map(key_of), target_key=edges["target"].map(key_of))
    e = e[e["actor_key"].notna() | e["target_key"].notna()].copy()
    e["source"] = "vbpl"
    overrides = load_overrides()
    by_number = dict(zip(docs["so_ky_hieu"], docs["doc_key"], strict=False))
    extra_edges = [
        {
            "actor": None,
            "target": None,
            "rel": str(Rel.REPLACES),
            "label": "override",
            "actor_key": by_number.get(o["replaced_by"]),
            "target_key": by_number.get(o["so_ky_hieu"]),
            "source": "override",
        }
        for o in overrides
        if o.get("replaced_by")
    ]
    rels = pd.concat([e, pd.DataFrame(extra_edges)], ignore_index=True)
    rels = rels.drop_duplicates(["actor", "target", "actor_key", "target_key", "rel"])
    # An actor issued before its target cannot amend/guide/replace it: keep but flag.
    issued = meta.set_index("id")["ngay_ban_hanh_dt"].to_dict()
    issued |= {r.doc_key: r.ngay_ban_hanh_dt for r in docs.itertuples()}
    a_date = rels["actor"].map(issued).fillna(rels["actor_key"].map(issued))
    t_date = rels["target"].map(issued).fillna(rels["target_key"].map(issued))
    directional = rels["rel"].isin(
        [
            Rel.REPLACES,
            Rel.REPEALS,
            Rel.REPEALS_PART,
            Rel.AMENDS,
            Rel.GUIDES,
            Rel.CONSOLIDATES,
            Rel.BASED_ON,
            Rel.CITES,
        ]
    )
    rels["suspect"] = directional & (a_date < t_date)

    # 5. effect status
    eff_any = meta.set_index("id")["ngay_co_hieu_luc_dt"].to_dict()
    eff_any |= {r.id: r.ngay_co_hieu_luc_dt for r in docs.itertuples()}
    repl = edges[edges["rel"] == Rel.REPLACES]
    replaced_by: dict[str, list] = {}
    for a, t in zip(repl["actor"], repl["target"], strict=True):
        tk = key_of.get(t)
        if tk:
            replaced_by.setdefault(tk, []).append((a, eff_any.get(a)))
    leg_status = (
        legacy_meta.assign(id=legacy_meta["id"])
        .set_index("id")[["effect_status", "effectless_date"]]
        .to_dict("index")
    )
    ov = {}
    for o in overrides:
        hits = docs[
            (docs["so_ky_hieu"] == o["so_ky_hieu"])
            & (docs["loai_van_ban"] == o.get("loai_van_ban", docs["loai_van_ban"]))
        ]
        for k in hits["doc_key"]:
            ov[k] = o
    res = [
        resolve_one(
            r._asdict(),
            as_of,
            replaced_by.get(r.doc_key, []),
            leg_status.get(int(r.legacy_id)) if pd.notna(r.legacy_id) else None,
            ov.get(r.doc_key),
        )
        for r in docs.itertuples()
    ]
    docs["status"] = [x["status"] for x in res]
    docs["status_source"] = [x["status_source"] for x in res]
    docs["status_flags"] = [x["status_flags"] for x in res]
    docs["ngay_co_hieu_luc_dt"] = [x["eff"] for x in res]
    docs["ngay_het_hieu_luc_dt"] = [x["exp"] for x in res]
    # Consolidated texts carry no status of their own: inherit from the consolidated document.
    cons = rels[(rels["rel"] == Rel.CONSOLIDATES) & rels["actor_key"].notna()]
    base_status = {}
    status_of = dict(zip(docs["doc_key"], docs["status"], strict=True))
    raw_status = meta.set_index("id")["tinh_trang_hieu_luc"].to_dict()
    for a, t, tk in zip(cons["actor_key"], cons["target"], cons["target_key"], strict=True):
        st = status_of.get(tk) if isinstance(tk, str) else None
        if st is None:
            st = RAW_MAP.get(raw_status.get(t, ""), None)
        if st and st != UNKNOWN:
            base_status.setdefault(a, st)
    vbhn = docs["loai_van_ban"].eq("Văn bản hợp nhất") & docs["status"].eq(UNKNOWN)
    docs.loc[vbhn, "status"] = docs.loc[vbhn, "doc_key"].map(base_status).fillna(UNKNOWN)
    docs.loc[vbhn & docs["status"].ne(UNKNOWN), "status_source"] = "consolidated_base"
    # Only the latest consolidation of a base document is current.
    base_of = dict(zip(cons["actor_key"], cons["target"], strict=False))
    is_vbhn = docs["loai_van_ban"].eq("Văn bản hợp nhất") & docs["doc_key"].isin(base_of)
    latest = (
        docs[is_vbhn]
        .assign(base=lambda t: t["doc_key"].map(base_of))
        .sort_values("ngay_ban_hanh_dt")
        .groupby("base")["doc_key"]
        .last()
    )
    old = is_vbhn & ~docs["doc_key"].isin(set(latest)) & docs["status"].eq(IN_FORCE)
    docs.loc[old, "status"] = "superseded"
    docs.loc[old, "status_source"] = "newer_consolidation"

    # 6. write
    keep = [
        "doc_key",
        "id",
        "legacy_id",
        "so_ky_hieu",
        "loai_van_ban",
        "title",
        "co_quan_ban_hanh",
        "ngay_ban_hanh_dt",
        "ngay_co_hieu_luc_dt",
        "ngay_het_hieu_luc_dt",
        "tinh_trang_hieu_luc",
        "status",
        "status_source",
        "status_flags",
        "domains",
        "hop_rank",
        "core",
        "content_source",
        "parse_clean",
        "parse_issues",
        "n_articles",
        "dropped_share",
        "attached_share",
        "preamble",
    ]
    docs = docs[keep].rename(
        columns={
            "id": "source_id",
            "ngay_ban_hanh_dt": "ngay_ban_hanh",
            "ngay_co_hieu_luc_dt": "ngay_co_hieu_luc",
            "ngay_het_hieu_luc_dt": "ngay_het_hieu_luc",
            "tinh_trang_hieu_luc": "status_raw",
        }
    )
    docs["parse_issues"] = docs["parse_issues"].map(
        lambda d: json.dumps(d if isinstance(d, dict) else {}, ensure_ascii=False)
    )
    docs.to_parquet(out_dir / "documents.parquet", index=False)
    units.to_parquet(out_dir / "units.parquet", index=False)
    rels.rename(columns={"actor": "actor_source_id", "target": "target_source_id"}).to_parquet(
        out_dir / "relations.parquet", index=False
    )
    print(f"wrote {len(docs)} documents, {len(units)} units, {len(rels)} relations to {out_dir}")

    write_report(docs, units, rels, args.report, as_of)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def write_report(
    docs: pd.DataFrame, units: pd.DataFrame, rels: pd.DataFrame, path: Path, as_of: pd.Timestamp
) -> None:
    parsed = docs[docs["content_source"] != "none"]
    with_art = parsed[parsed["n_articles"] > 0]
    issues = Counter()
    for d in parsed["parse_issues"]:
        issues.update({k: 1 for k in json.loads(d)})
    by_type = parsed.groupby("loai_van_ban").agg(
        n=("doc_key", "size"),
        sạch=("parse_clean", "mean"),
        điều_tb=("n_articles", "mean"),
        bỏ_tb=("dropped_share", "mean"),
        đính_kèm_tb=("attached_share", "mean"),
    )
    by_type["sạch"] = (by_type["sạch"] * 100).round(1).astype(str) + "%"
    by_src = parsed.groupby("content_source")["parse_clean"].agg(["size", "mean"])
    by_src["mean"] = (by_src["mean"] * 100).round(1).astype(str) + "%"
    dom = (
        docs.explode("domains")
        .groupby("domains")
        .agg(
            văn_bản=("doc_key", "size"),
            còn_HL=("status", lambda s: (s == IN_FORCE).sum()),
            có_toàn_văn=("content_source", lambda s: (s != "none").sum()),
            parse_sạch=("parse_clean", lambda s: f"{100 * s.fillna(False).mean():.0f}%"),
        )
    )
    flags = Counter(f for fl in docs["status_flags"] for f in fl)
    anchors = docs[docs["hop_rank"].eq(0) & docs["loai_van_ban"].isin(["Luật", "Bộ luật"])]
    anchors = anchors.sort_values("ngay_ban_hanh")[
        [
            "doc_key",
            "status",
            "status_source",
            "ngay_co_hieu_luc",
            "ngay_het_hieu_luc",
            "content_source",
            "n_articles",
            "parse_clean",
            "domains",
        ]
    ].copy()
    for c in ["ngay_co_hieu_luc", "ngay_het_hieu_luc"]:
        anchors[c] = pd.to_datetime(anchors[c]).dt.strftime("%d/%m/%Y")
    review = parsed[
        ~parsed["parse_clean"].astype(bool)
        & parsed["loai_van_ban"].isin(["Luật", "Bộ luật", "Nghị định"])
    ]
    review = review[["doc_key", "loai_van_ban", "n_articles", "parse_issues", "content_source"]]

    text = (
        f"""# Báo cáo chất lượng dữ liệu (bước 3)

_Sinh tự động bởi `scripts/ingest.py` — không sửa tay._ Trạng thái hiệu lực tính tại ngày
{as_of.date()} (dữ liệu nguồn snapshot 2026-07-23).

## 1. Tổng quan

- Lĩnh vực: {", ".join(CORE_DOMAINS)}
- Văn bản: **{len(docs):,}**. Có toàn văn: {len(parsed):,}, gồm {int((docs.content_source == "vbpl_html").sum())}
  từ HTML vbpl và {int((docs.content_source == "legacy_text").sum())} từ bản crawl cũ. Không có toàn
  văn: {int((docs.content_source == "none").sum())}.
- Đơn vị: {len(units):,}, theo loại: {units["kind"].value_counts().to_dict()}
- Quan hệ chạm tới corpus: {len(rels):,}, cả hai đầu trong corpus:
  {int((rels.actor_key.notna() & rels.target_key.notna()).sum()):,}. Cạnh nghi vấn (bên tác động
  ban hành trước bên bị tác động): {int(rels["suspect"].sum())}, theo loại:
  {rels[rels["suspect"]]["rel"].value_counts().to_dict()}

{dom.to_markdown()}

## 2. Parse

**Parse sạch: {pct(parsed["parse_clean"].mean())}** trên văn bản có toàn văn. Tính riêng văn bản có ít
nhất một Điều: {pct(with_art["parse_clean"].mean())}. "Sạch" nghĩa là có Điều, số Điều liên tục bắt đầu
từ 1, không có điều rỗng, không có dòng "Điều N" bị loại ngoài ngoặc kép, ngoặc kép cân bằng và id
không trùng. Parser không bỏ dòng nào ngoài dòng chữ ký / nơi nhận: `bỏ_tb` = tỉ lệ ký tự bị bỏ;
`đính_kèm_tb` = tỉ lệ ký tự nằm trong phần đính kèm sau chữ ký (`#kt{{n}}`). Văn bản có phần đính
kèm > 50% mà vẫn có Điều: {int(((parsed["attached_share"] > 0.5) & (parsed["n_articles"] > 0)).sum())}
(đã soát tay lần chạy 2026-11-11: đều là biểu giá / danh mục / mẫu đính kèm hợp lệ, không phải
nhận nhầm khối chữ ký).

### Theo loại văn bản

{by_type.round(2).to_markdown()}

### Theo nguồn toàn văn

{by_src.rename(columns={"size": "n", "mean": "sạch"}).to_markdown()}

### Lỗi hay gặp (số văn bản)

| lỗi | số văn bản | ý nghĩa |
|---|---|---|
"""
        + "\n".join(f"| `{k}` | {v} | {ISSUE_DOC.get(k, '')} |" for k, v in issues.most_common())
        + f"""

### Luật / Bộ luật / Nghị định chưa sạch (cần xem tay)

{review.head(40).to_markdown(index=False)}

## 3. Hiệu lực

{pd.crosstab(docs["status"], docs["status_source"]).to_markdown()}

Cờ cần xem lại: {dict(flags.most_common())}

### Luật gốc

{anchors.to_markdown(index=False)}
"""
    )
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")


ISSUE_DOC = {
    "rejected_article": "dòng 'Điều N' sai thứ tự ngoài ngoặc kép (thường là trích dẫn thiếu ngoặc)",
    "no_articles": "văn bản không có Điều (lưu thành một đơn vị #body)",
    "article_gap": "nhảy 1 số Điều (nguồn thiếu điều hoặc lỗi gõ)",
    "first_article_not_1": "Điều đầu tiên không phải Điều 1",
    "unbalanced_quote": "ngoặc kép mở mà không đóng tới cuối văn bản",
    "unclosed_quote_recovered": "ngoặc không đóng, đã tự phục hồi ở điều kế tiếp",
    "duplicate_id": "id đơn vị trùng (đã thêm hậu tố _2)",
    "empty_article": "Điều chỉ có tiêu đề rỗng",
}


if __name__ == "__main__":
    main()

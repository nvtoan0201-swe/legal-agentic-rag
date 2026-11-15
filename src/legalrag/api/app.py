"""HTTP API + a one-page demo UI.

    uv run uvicorn legalrag.api.app:app --port 8080      # then open http://localhost:8080

Without an LLM configured the agent still retrieves, filters, expands and gates, and the answer is
the best passage quoted with its citation (mode "extractive").
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from legalrag.config import settings

DISCLAIMER = (
    "Công cụ tham khảo phục vụ học tập, nghiên cứu. Không thay thế tư vấn pháp lý; luôn đối chiếu "
    "văn bản gốc."
)

app = FastAPI(title="legal-agentic-rag", description=DISCLAIMER)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    as_of: date | None = None


class Citation(BaseModel):
    unit_id: str
    label: str
    text: str
    status: str | None


class AskResponse(BaseModel):
    answer: str
    abstained: bool
    citations: list[Citation]
    mode: str  # llm | extractive
    trace: list[str]
    disclaimer: str = DISCLAIMER


class SearchHit(BaseModel):
    unit_id: str
    score: float
    status: str | None
    text: str


@lru_cache(maxsize=1)
def _system():
    from legalrag.baselines.rag import ExtractiveGenerator, Generator
    from legalrag.graph.agent import Agent, AgentConfig
    from legalrag.graph.links import Links
    from legalrag.retrieval.retriever import Retriever
    from legalrag.store import Corpus

    corpus = Corpus.load(Path(settings.data_dir) / "processed")
    retriever = Retriever.from_disk(Path(settings.data_dir) / "index", corpus=corpus)
    links = Links.build(corpus.docs.reset_index(drop=True), corpus.units)
    cfg = AgentConfig()
    res = Path(settings.data_dir) / "eval/results/agent.json"
    if res.exists():  # threshold calibrated by scripts/eval_agent.py
        cfg = replace(cfg, gate_threshold=json.loads(res.read_text())["threshold"])
    if settings.llm_api_key:
        from legalrag.llm import complete

        agent = Agent(retriever, corpus, links, Generator(complete), complete, cfg)
        return agent, "llm"
    return Agent(retriever, corpus, links, ExtractiveGenerator(n=2), None, cfg), "extractive"


@app.get("/health")
def health() -> dict:
    return {"ok": True, "llm": bool(settings.llm_api_key)}


@app.post("/search", response_model=list[SearchHit])
def search(req: AskRequest) -> list[SearchHit]:
    agent, _ = _system()
    s = agent.search(req.question, req.as_of)
    return [
        SearchHit(
            unit_id=h.unit_id, score=h.score, status=agent.corpus.status(h.doc_key), text=h.text
        )
        for h in s["hits"][:10]
    ]


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    agent, mode = _system()
    s = agent.run(req.question, req.as_of)
    ans = s["answer"]
    by_id = {p.unit_id: p for p in s.get("passages", [])}
    cites = []
    for c in ans.citations:
        p = by_id.get(c)
        cites.append(
            Citation(
                unit_id=c,
                label=p.label if p else agent.corpus.title(c.split("#")[0]),
                text=p.text if p else agent.corpus.passage(c),
                status=agent.corpus.status(c.split("#")[0]),
            )
        )
    return AskResponse(
        answer=ans.text,
        abstained=bool(ans.abstained),
        citations=cites,
        mode=mode,
        trace=s.get("trace", []),
    )


PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tra cứu pháp luật — Agentic RAG</title>
<style>
body{font:15px/1.55 system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.3rem}textarea{width:100%;min-height:4.5rem;font:inherit;padding:.6rem;box-sizing:border-box}
button{font:inherit;padding:.45rem 1.1rem;margin-top:.5rem;cursor:pointer}
.warn{background:#fff6e0;border-left:4px solid #e0a400;padding:.5rem .8rem;font-size:.9rem}
.ans{white-space:pre-wrap;background:#f5f7fa;padding:.9rem;border-radius:6px;margin-top:1rem}
.cite{border:1px solid #dde2ea;border-radius:6px;padding:.6rem .8rem;margin:.6rem 0}
.cite b{font-family:ui-monospace,monospace}.exp{color:#b00020;font-weight:600}
details{margin-top:1rem;font-size:.85rem;color:#555}pre{white-space:pre-wrap}
</style></head><body>
<h1>Trợ lý tra cứu pháp luật Việt Nam (Agentic RAG)</h1>
<p class="warn">__DISCLAIMER__</p>
<textarea id="q"
 placeholder="Ví dụ: Tôi đang nuôi con 8 tháng, công ty có được cho tôi nghỉ việc không?">
</textarea>
<div>Ngày áp dụng (tuỳ chọn): <input type="date" id="d"> <button onclick="go()">Hỏi</button></div>
<div id="out"></div>
<script>
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
async function go(){
  const q=document.getElementById('q').value.trim(); if(!q) return;
  const d=document.getElementById('d').value||null, out=document.getElementById('out');
  out.innerHTML='<p>Đang tra cứu…</p>';
  const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({question:q,as_of:d})});
  const j=await r.json();
  let h='<div class="ans">'+esc(j.answer)+'</div>';
  if(j.mode==='extractive') h+='<p class="warn">Chế độ không có LLM: hiển thị điều khoản '+
    'phù hợp nhất thay cho câu trả lời.</p>';
  for(const c of j.citations){
    h+='<div class="cite"><b>'+esc(c.unit_id)+'</b> — '+esc(c.label)+
       (c.status&&c.status!=='in_force'?' <span class="exp">('+esc(c.status)+')</span>':'')+
       '<pre>'+esc(c.text)+'</pre></div>';
  }
  h+='<details><summary>Các bước của agent</summary><pre>'+
    esc(j.trace.join('\\n'))+'</pre></details>';
  out.innerHTML=h;
}
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE.replace("__DISCLAIMER__", DISCLAIMER)

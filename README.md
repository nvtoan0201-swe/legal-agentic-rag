# legal-agentic-rag

Trợ lý tra cứu pháp luật Việt Nam bằng Agentic RAG.

> ⚠️ **Cảnh báo:** Đây là công cụ tham khảo phục vụ học tập và nghiên cứu. Kết quả có thể
> sai, thiếu hoặc dựa trên văn bản đã hết hiệu lực. **Không thay thế tư vấn pháp lý** của luật
> sư hoặc cơ quan có thẩm quyền. Luôn đối chiếu với văn bản gốc trên Công báo /
> Cơ sở dữ liệu quốc gia về văn bản pháp luật trước khi sử dụng.

## Mục tiêu

- Trả lời có **trích dẫn tới Điều/Khoản/Điểm** (vd: `45/2019/QH14#d35-k2`).
- Dùng đúng **văn bản còn hiệu lực** tại thời điểm hỏi.
- **Abstain** (từ chối trả lời) khi không đủ căn cứ.
- Mọi thành phần agentic phải được chứng minh bằng eval:
  baseline → phân tích lỗi → thêm thành phần → ablation.

## Cấu trúc

```
src/legalrag/
  ingest/      tải, lọc, parse Chương → Điều → Khoản → Điểm
  index/       chỉ mục Qdrant / BM25
  retrieval/   dense, sparse, hybrid, rerank
  graph/       agent LangGraph (tuần 3+)
  baselines/   RAG không agentic
  api/         FastAPI (sau này)
eval/          bộ câu hỏi, loader, metric
scripts/       script chạy một lần (khám phá dữ liệu, build index...)
tests/
reports/       báo cáo khám phá / chất lượng dữ liệu (không chứa dữ liệu thô)
data/          dữ liệu tải về — bị .gitignore, không commit
```

## Bắt đầu

```bash
make install            # uv sync
cp .env.example .env    # điền LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
make up                 # Qdrant + Postgres
make test lint
```

LLM được gọi qua endpoint tương thích OpenAI (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`).

## Dữ liệu và giấy phép

<!-- LICENSE-SECTION -->
_Đang kiểm tra (bước 2)._

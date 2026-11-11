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

### Corpus: [th1nhng0/vietnamese-legal-documents](https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents)

- **Giấy phép:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) cho phần dataset đã biên
  soạn (schema, xử lý, tuyển chọn). Bản thân văn bản quy phạm pháp luật là tài sản công theo
  Luật Tiếp cận thông tin 104/2016/QH13 và Luật Ban hành văn bản QPPL 64/2025/QH15 (theo dataset card).
- **Nghĩa vụ:** ghi công tác giả khi dùng lại / phân phối lại dữ liệu đã xử lý:

  ```bibtex
  @dataset{ngo_thinh_2026_vietnamese_legal,
    title     = {Vietnamese Legal Documents},
    author    = {Thịnh Ngô},
    year      = {2026},
    publisher = {Hugging Face},
    url       = {https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents},
    doi       = {10.57967/hf/8598},
  }
  ```

- **Nguồn gốc:** crawl từ [vbpl.vn](https://vbpl.vn) (Cơ sở dữ liệu quốc gia về văn bản pháp luật,
  Bộ Tư pháp), snapshot ngày 2026-07-23. Tình trạng hiệu lực phản ánh thời điểm crawl, có thể trễ
  so với thực tế. Repo dùng revision `8977887f17be2defae4c5171d55562e1cde7d695`.

### Bộ QA: [thangvip/vietnamese-legal-qa](https://huggingface.co/datasets/thangvip/vietnamese-legal-qa)

- **Giấy phép: không khai báo** trên dataset card (kiểm tra 2026-11-11). Chỉ dùng nội bộ để
  đánh giá; không phân phối lại cho tới khi tác giả làm rõ giấy phép.
- Câu hỏi/đáp án do LLM sinh tự động từ nội dung điều luật, nên cần duyệt lại trước khi làm gold.

Dữ liệu tải về nằm trong `data/` và **không được commit**.

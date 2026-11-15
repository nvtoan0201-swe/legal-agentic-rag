# legal-agentic-rag

Trợ lý tra cứu pháp luật Việt Nam bằng Agentic RAG: trả lời có trích dẫn tới Điều/Khoản, chỉ dùng
văn bản còn hiệu lực, từ chối khi không đủ căn cứ.

> ⚠️ Công cụ tham khảo cho học tập, nghiên cứu. Không thay thế tư vấn pháp lý.

## Thành phần

- **Corpus:** 1.604 văn bản thuộc 6 lĩnh vực (lao động, BHXH, HN&GĐ, giao thông, đất đai, thuế TNCN),
  tách thành Chương/Điều/Khoản/Điểm, nạp vào Postgres.
- **Truy xuất:** BM25 + dense (bge-m3, Qdrant) + RRF, rerank bằng bge-reranker-v2-m3.
- **Agent (LangGraph):** phân tích câu hỏi → tìm kiếm có lọc hiệu lực → mở rộng theo dẫn chiếu giữa
  các điều khoản → từ chối nếu bằng chứng yếu → sinh câu trả lời → kiểm tra trích dẫn.
- **Eval:** bộ câu hỏi tự động + 66 câu tình huống; ablation từng thành phần.
- **Demo:** FastAPI + trang web.

## Chạy

```bash
cp .env.example .env    # điền LLM_BASE_URL, LLM_MODEL, LLM_API_KEY (tuỳ chọn)
make install up
make ingest load-db     # xây corpus
make index              # BM25 + vector
make eval-retrieval eval-agent
make serve              # http://localhost:8080
```

## Kết quả truy xuất

Recall@5 ở mức Điều. `situational` là câu hỏi tình huống, không nêu số Điều.

| Cấu hình | situational (56) | lqa test (186) | luật cũ → luật mới (153) |
|---|---|---|---|
| BM25 | 0,491 | 0,952 | 0,647 |
| Dense | 0,536 | 0,968 | 0,765 |
| Hybrid | 0,562 | 0,962 | 0,725 |
| Hybrid + rerank | 0,661 | 0,989 | 0,693 |
| Hybrid + rerank + lọc hiệu lực | **0,812** | **0,995** | **0,876** |

Kết quả trả lời đầu cuối (cần LLM) chưa chạy.

## Dữ liệu

- Corpus: [th1nhng0/vietnamese-legal-documents](https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents)
  (CC BY 4.0, Thịnh Ngô 2026, doi:10.57967/hf/8598), crawl từ vbpl.vn.
- Bộ QA: [thangvip/vietnamese-legal-qa](https://huggingface.co/datasets/thangvip/vietnamese-legal-qa)
  (chưa khai báo giấy phép, chỉ dùng nội bộ để đánh giá).
- Dữ liệu tải về nằm trong `data/`, không commit.

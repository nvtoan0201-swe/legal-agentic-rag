# Bộ eval

Code nằm ở `src/legalrag/eval/`. Thư mục này chỉ chứa các bộ câu hỏi **được commit**: câu tự viết
và câu nháp đã duyệt. Bộ sinh từ `thangvip/vietnamese-legal-qa` (không khai báo giấy phép) và nháp
chưa duyệt nằm trong `data/eval/`, không commit.

| file | nguồn | commit |
|---|---|---|
| `eval/sets/manual_template.jsonl` | 4 ví dụ mẫu, một ví dụ cho mỗi loại | có |
| `eval/sets/manual.jsonl` | ~100 câu khó bạn tự viết | có |
| `eval/sets/reviewed_drafts.jsonl` | nháp LLM đã duyệt | có |
| `data/eval/legal_qa.jsonl` | `make eval-data` | không |
| `data/eval/drafts/*.jsonl` | `scripts/gen_drafts.py` | không |

## Định dạng (một JSON mỗi dòng)

| trường | ý nghĩa |
|---|---|
| `id` | duy nhất; câu tự viết dùng `man-0001`… |
| `question` | câu hỏi như người dân hỏi |
| `category` | `single_hop` · `multi_hop` · `expired` · `out_of_scope` |
| `expected_behavior` | `answer` · `answer_current` (trả lời theo văn bản hiện hành) · `abstain` |
| `gold_articles` | id đơn vị đủ để trả lời, ví dụ `45/2019/QH14#d35-k1-a`. Chấm truy xuất ở mức Điều |
| `gold_answer` | đáp án ngắn có trích dẫn `[id]` (để chấm correctness) |
| `forbidden_articles` | điều khoản **không được** dùng làm căn cứ hiện hành (điều của luật đã hết hiệu lực) |
| `domain` | `lao_dong` · `bhxh` · `hon_nhan_gia_dinh` · `giao_thong_duong_bo` · `dat_dai` · `thue_tncn` |
| `as_of` | ngày đặt câu hỏi, để xác định văn bản nào còn hiệu lực |
| `source` | `manual` · `llm_draft` · `thangvip/vietnamese-legal-qa` |
| `reviewed` | đã có người kiểm tra gold hay chưa |

Id đơn vị: `{số hiệu}#d{điều}[-k{khoản}][-{điểm}]`, điểm `đ` viết là `dd`; phụ lục `#pl1`; phần đính
kèm sau chữ ký `#kt1`, điều trong đó `#kt1-d3`. Tìm id bằng SQL:

```sql
SELECT unit_id, left(text, 150) FROM units
WHERE doc_key = '45/2019/QH14' AND text ILIKE '%báo trước%';
```

## Gợi ý viết ~100 câu khó

Phân bổ đề xuất: 30 `single_hop` khó · 30 `multi_hop` · 20 `expired` · 20 `out_of_scope`. Mỗi lĩnh
vực ít nhất 12 câu, **ưu tiên lao động, HN&GĐ, đất đai, thuế TNCN** (bộ QA tự động không có câu nào
về các lĩnh vực này).

- **Không đưa đường tắt vào câu hỏi:** không nêu số điều, số hiệu, năm ban hành. Viết theo tình huống
  ("Tôi…", "Công ty tôi…").
- **single_hop khó:** câu hỏi diễn đạt khác hẳn từ ngữ trong luật, có ngoại lệ ("trừ trường hợp…"),
  điều kiện về số, ngày hoặc mức tiền.
- **multi_hop:** cần luật + nghị định/thông tư hướng dẫn, hoặc hai điều của cùng một luật (định
  nghĩa ở Điều 3 + quy định ở Điều 35). Ghi đủ mọi id cần thiết vào `gold_articles`.
- **expired:** chọn chỗ luật mới khác luật cũ (ví dụ nồng độ cồn, tuổi nghỉ hưu, thời gian đóng BHXH
  tối thiểu, thuế TNCN từ 01/07/2026). `gold_articles` = điều mới; `forbidden_articles` = điều cũ.
  Danh sách cặp điều cũ–mới gợi ý có trong `data/eval/drafts/version_prompts.jsonl`.
- **out_of_scope:** thuộc lĩnh vực khác (hình sự, sở hữu trí tuệ, doanh nghiệp…) **hoặc** cùng chủ đề
  nhưng corpus không có căn cứ (chi tiết thủ tục ở một địa phương cụ thể). Hệ thống phải từ chối.

Kiểm tra trước khi commit: `uv run python -I scripts/check_eval_set.py eval/sets/manual.jsonl`
(kiểm tra schema, id có tồn tại trong corpus, cảnh báo nếu gold rơi vào văn bản hết hiệu lực).

## Sinh nháp multi-hop / version bằng LLM

```bash
# cần LLM_BASE_URL, LLM_MODEL, LLM_API_KEY trong .env
uv run python -I scripts/gen_drafts.py --kind multihop --per-domain 15
uv run python -I scripts/gen_drafts.py --kind version --per-domain 10
```

Cặp **multihop** là điều của nghị định/thông tư dẫn chiếu rõ "khoản M Điều N của <luật>", ghép với
chính điều đó của luật. Cặp **version** là các điều cùng tiêu đề giữa luật cũ và luật thay thế mà
nội dung đã đổi. Nháp ghi `reviewed=false`. Khi duyệt: sửa câu hỏi, kiểm gold, đặt
`reviewed=true`, rồi chuyển câu tốt vào `eval/sets/reviewed_drafts.jsonl`.

## Metric

- Truy xuất (`legalrag.eval.metrics`): Recall@k, MRR, nDCG@k, chấm ở mức Điều theo mặc định (`level=`
  `unit` / `article` / `document`). Câu không có gold (out_of_scope, expired chưa duyệt) bị bỏ qua.
- Câu trả lời (`legalrag.eval.generation`):
  - độ đúng trích dẫn (precision/recall ở mức Điều);
  - `cites_forbidden` và `cites_expired`;
  - abstain precision/recall/F1 và tỉ lệ từ chối thừa;
  - correctness và faithfulness chấm bằng LLM-judge.

# Bước 2 — Tóm tắt khám phá dữ liệu

Chi tiết số liệu: [data_exploration.md](data_exploration.md) (metadata + quan hệ) và
[fulltext_samples.md](fulltext_samples.md) (20 văn bản mẫu, tỉ lệ rỗng, ước lượng kích thước).
Tái tạo: `make explore` rồi `make sample`.

## Dataset

`th1nhng0/vietnamese-legal-documents`, CC BY 4.0, crawl từ vbpl.vn, snapshot 2026-07-23.

| config | dòng | kích thước | ghi chú |
|---|---|---|---|
| metadata | 171.556 | 15 MB | 17 cột, tiếng Việt |
| relationships | 1.033.255 | 9 MB | quan hệ mức văn bản |
| content | 170.824 | 785 MB | **HTML thô**, 35 row group |
| legacy_metadata | 518.601 | 51 MB | crawl cũ (~03/2026), hệ id khác |
| legacy_content | 518.235 | 3,5 GB | plain text, 1 row group |

Văn bản trung ương có tính quy phạm (Luật, NĐ, TT, TTLT, NQ/QĐ trung ương, VBHN): **42.899**.

## Phát hiện chính

### Metadata
1. **Không lọc lĩnh vực theo metadata được.** `linh_vuc` thiếu 69% ("Chưa phân loại"), `nganh` thiếu
   38%. Luật mới nhất (Luật Đất đai 2024, Luật TTATGTĐB) để trống cả hai trường, và tiêu đề của chúng
   chỉ còn "Đất đai", "doanh nghiệp". → Phạm vi lĩnh vực xác định bằng **luật gốc + đồ thị quan hệ**
   (`src/legalrag/ingest/domains.py`).
2. **`so_ky_hieu` không phải khoá duy nhất.** 4.853 dòng (trung ương, quy phạm) trùng cả số hiệu lẫn
   loại; có cặp trùng mà một bản rỗng, một bản đủ (59/2020/QH14: id 142847 rỗng / 142881 đủ). → Id ổn
   định của điều khoản nên dựa vào `so_ky_hieu`, kèm bước khử trùng chọn bản có nội dung.
3. Ngày tháng định dạng sạch (0% parse lỗi). Thiếu: `ngay_co_hieu_luc` 2,9%, `ngay_het_hieu_luc` 53%
   (bình thường với văn bản còn hiệu lực), `thong_tin_ap_dung` trống 100%.

### Hiệu lực: có trường, nhưng chỉ tin được ở mức vừa phải
- Có `tinh_trang_hieu_luc` (8 giá trị), `ngay_co_hieu_luc`, `ngay_het_hieu_luc`. **Không có hiệu lực
  ở mức Điều/Khoản**: "Hết hiệu lực một phần" không cho biết phần nào.
- Nhất quán nội bộ: 11,9% văn bản "Hết hiệu lực toàn bộ" thiếu ngày hết hiệu lực; 1,9% có ngày hiệu
  lực trước ngày ban hành.
- So với đồ thị: 1.143 / 14.688 văn bản đã bị thay thế/bãi bỏ (bởi văn bản đã có hiệu lực) vẫn ghi
  "Còn hiệu lực".
- So với bản crawl cũ: hai bản đồng ý 87,7%. Ở cả hai chiều đều có chỗ bản hiện tại sai: Luật Cư trú
  sửa đổi 2013 và Luật Tổ chức TAND 2014 vẫn ghi "Còn hiệu lực".
- Đối chiếu tay 12 luật quen thuộc: 4 chỗ lệch. Luật Đất đai 2024 ghi hiệu lực 01/01/2025, thực tế là
  01/08/2024; Luật Đất đai 2013 ghi hết hiệu lực 01/01/2025, thực tế là 01/08/2024. Luật BHXH 2024 bị
  ghi "Hết hiệu lực toàn bộ 01/01/2026", trong khi bản cũ ghi "In effect"; **cần kiểm chứng trên
  vbpl.vn**. Luật GTĐB 2008 thiếu ngày hết hiệu lực.
- Văn bản hợp nhất luôn ghi "Chưa xác định": trạng thái phải lấy theo luật gốc.
- → Đề xuất cho bước 3: tính trạng thái hiệu lực từ **nhiều nguồn** (metadata + cạnh thay thế/bãi
  bỏ + legacy). Khi các nguồn lệch nhau thì gắn cờ, và **ghi đè tay cho các luật gốc** của lĩnh vực đã
  chọn (khoảng 30 văn bản, kiểm trên vbpl.vn).

### Quan hệ
- 31 nhãn trộn hai bộ từ vựng: nhãn hành động ("Thay thế") và nhãn vai trò ("Văn bản sửa đổi" = bên
  kia sửa đổi mình). Kiểm bằng ngày ban hành thì chiều quan hệ cực rõ (≥99% hoặc ≤1% với mọi nhãn
  lớn), nên chuẩn hoá được thành 10 loại actor → target (`relations.py`).
- 4,2% cạnh trỏ ra ngoài metadata. Quan hệ chỉ ở **mức văn bản**: không biết điều nào sửa điều nào.

### Toàn văn
- HTML vbpl.vn khá sạch: mỗi đoạn một `<p>`, tiêu đề Điều/Chương in đậm, quốc hiệu và chữ kí nằm
  trong bảng. Không phải markdown.
- **Rỗng 8,6%** (trên 30.824 văn bản ≈ 18% corpus). Tỉ lệ rỗng cao ở: **văn bản hợp nhất 91%**, văn
  bản 2020–2026 khoảng 20–25%, Luật Đất đai 2024 (luật gốc quan trọng!). Bản cũ có Luật Đất đai 2024
  và Luật thuế TNCN 2007 (config chính không có luật này), nhưng phải tải trọn 3,5 GB.
- Cấu trúc Chương → Mục → Điều → Khoản → Điểm khá đều ở Luật/NĐ/TT gần đây. Những trường hợp khó
  parser phải xử lý:
  - **Lỗi chính tả tiêu đề**: "Điêu 38" (Luật BHXH 2024), nên regex phải chịu được dấu sai.
  - **Văn bản sửa đổi** (vd 81/2025/QH15): nội dung điều được sửa trích trong ngoặc kép, nhưng **có dòng
    thiếu dấu mở ngoặc** ("Điều 55." nằm trong Điều 1). Không thể chỉ dựa vào dấu ngoặc.
  - **Phụ lục / biểu mẫu** (145/2020/NĐ-CP): trong mẫu quyết định lại có "Điều 1." nên phải dừng parse
    điều khi gặp "Phụ lục"/"Mẫu số".
  - **Điểm lồng nhiều cấp**: "b.1)", "b.1.1)" (111/2013/TT-BTC có 300 dòng), sâu hơn Điểm.
  - Văn bản cũ: "Điều 1:" dùng dấu hai chấm; luật 1990 không có dấu chấm sau số điều.
  - Điều không có khoản (rất phổ biến), đoạn văn không đánh số nằm giữa các khoản, gạch đầu dòng, bảng
    (mức phạt, danh mục), dòng tiêu đề Điều đôi khi dính luôn đoạn đầu.
  - NQ/QĐ cá biệt (vd điều chỉnh quy hoạch sử dụng đất của một tỉnh) gần như chỉ có bảng và không có
    giá trị hỏi đáp. → lọc theo tiêu đề.

## Đề xuất lĩnh vực

Số văn bản = luật gốc + hop 1 + hop 2 + tiền nhiệm, chỉ tính văn bản trung ương có tính quy phạm.
MB text là ước lượng thô từ mẫu.

| # | lĩnh vực | văn bản | có toàn văn (ước) | MB text | lí do | rủi ro |
|---|---|---|---|---|---|---|
| 1 | Lao động | 430 | ~400 | ~8 | BLLĐ 2019 + NĐ 145/2020, BLLĐ 2012 làm câu "hết hiệu lực", rỗng 2% | — |
| 2 | BHXH | 163 | ~150 | ~3 | Luật 2024 thay Luật 2014 từ 1/7/2025: rất hợp câu hỏi phiên bản | trạng thái Luật 2024 mâu thuẫn |
| 3 | Hôn nhân gia đình | 96 | ~80 | ~2 | luật ổn định từ 2014, dễ làm single-hop | ít văn bản hướng dẫn |
| 4 | Giao thông đường bộ | 411 | ~370 | ~6 | Luật 2008 tách thành 2 luật từ 1/1/2025; nhu cầu hỏi cao (xử phạt) | nhiều TT kĩ thuật |
| 5 | Đất đai | 535 | ~490 | ~8 | nhu cầu cao, có 2013 → 2024 | toàn văn Luật 2024 rỗng, ngày hiệu lực sai, có NQ quy hoạch cá biệt |
| 6 | Thuế TNCN | 99 | ~70 | ~1,4 | Luật mới 109/2025 hiệu lực 1/7/2026, sửa đổi 09/2026: rất hợp câu hỏi thời điểm | thiếu luật 2007, mẫu rỗng 38%, VBHN rỗng |
| 7 | (tuỳ chọn) Doanh nghiệp | 277 nếu chỉ hop ≤ 1 | — | ~4 | Luật DN 2020 rất hay hỏi | đủ hop 2 lên 900 văn bản, nhiễu |

**Khuyến nghị: lấy 6 lĩnh vực đầu.** Sau khi bỏ trùng còn **1.633 văn bản** (814 TT, 371 NĐ, 53 Luật,
98 VBHN, …), khoảng **25–30 MB text**. Corpus đủ nhỏ để parse, kiểm tay và index nhanh, mà vẫn
có đủ bốn nhóm câu eval (single-hop, multi-hop qua quan hệ hướng dẫn, văn bản hết hiệu lực, ngoài phạm
vi). Thêm Doanh nghiệp (hop ≤ 1) thì tổng là 1.881 văn bản.

Không khuyến nghị: Nhà ở (rỗng 28%), Cư trú (chỉ 30 văn bản), BHYT (chồng lấn BHXH; có thể thêm sau).

## Quyết định cần bạn duyệt trước bước 3

1. **Danh sách lĩnh vực** (6 lĩnh vực trên, có thêm Doanh nghiệp không?).
2. **Nguồn dự phòng cho toàn văn rỗng**: (a) tải `legacy_content` 3,5 GB và ghép theo số hiệu + ngày;
   (b) tự crawl vbpl.vn cho vài chục văn bản thiếu; (c) chấp nhận thiếu và ghi vào báo cáo chất lượng.
   Văn bản then chốt đang rỗng: Luật Đất đai 2024, các VBHN.
3. **Ghi đè tay trạng thái hiệu lực** cho các luật gốc (một file YAML nhỏ trong repo, có nguồn), được
   không?

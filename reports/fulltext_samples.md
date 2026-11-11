# Mẫu toàn văn: th1nhng0/vietnamese-legal-documents (config `content`)

_Sinh tự động bởi `scripts/sample_fulltext.py` — không sửa tay._

Đã tải 7/35 row group (30,824 văn bản, 18% corpus) chứa các văn bản
mẫu cố định. Thống kê rỗng/độ dài dưới đây tính trên toàn bộ các dòng đó. "Rỗng" = text sau khi bỏ
HTML < 200 ký tự.

## 1. Định dạng

- Cột `content_html`: HTML thô của vbpl.vn, không phải markdown. Nội dung bọc trong
  `<table class="detailcontent">`, mỗi đoạn là một `<p>`, tiêu đề Điều/Chương in `<strong>`.
- Chuyển sang dòng văn bản bằng `legalrag.ingest.html.html_to_lines` (bảng → `| ô | ô |`).

## 2. 20 văn bản mẫu

| id                                   | số hiệu              | loại               |   năm | lĩnh vực              |   dòng |   ký tự |   chương |   mục |   điều |   điều (lỏng) | điều tăng dần   |   điều không khoản |   khoản |   khoản kiểu 1) |   điểm a) |   điểm a. |   gạch đầu dòng |   dòng bảng |   phụ lục |   dòng trích dẫn “ | có quốc hiệu   |
|:-------------------------------------|:---------------------|:-------------------|------:|:----------------------|-------:|--------:|---------:|------:|-------:|--------------:|:----------------|-------------------:|--------:|----------------:|----------:|----------:|----------------:|------------:|----------:|-------------------:|:---------------|
| 139264                               | 45/2019/QH14         | Bộ luật            |  2019 | bhxh,lao_dong         |   1360 |  188093 |       17 |    24 |    220 |           220 | ✓               |                 37 |     645 |               0 |       287 |         0 |               0 |           4 |         0 |                  4 | ✓              |
| 36870                                | 52/2014/QH13         | Luật               |  2014 | hon_nhan_gia_dinh     |    617 |   86094 |        9 |     7 |    133 |           133 | ✓               |                 39 |     294 |               0 |        80 |         0 |               0 |           3 |         0 |                  0 | ✓              |
| 142881                               | 59/2020/QH14         | Luật               |  2020 | doanh_nghiep,lao_dong |   2006 |  318274 |       10 |     2 |    218 |           218 | ✓               |                 10 |     897 |               0 |       822 |         0 |               0 |           0 |         0 |                  0 | ✓              |
| 170620                               | 36/2024/QH15         | Luật               |  2024 | giao_thong_duong_bo   |   1011 |  161959 |        9 |     0 |     89 |            89 | ✓               |                  1 |     440 |               0 |       443 |         0 |               0 |           0 |         0 |                  0 | ✓              |
| 175027                               | 41/2024/QH15         | Luật               |  2024 | bhxh,lao_dong         |   1180 |  182153 |       11 |    13 |    140 |           140 | ✗               |                 10 |     543 |               0 |       359 |         0 |               0 |           0 |         0 |                  7 | ✓              |
| 187045                               | 109/2025/QH15        | Luật               |  2025 | thue_tncn             |    236 |   29366 |        4 |     0 |     29 |            29 | ✓               |                  5 |     111 |               0 |        59 |         0 |               0 |          11 |         0 |                  0 | ✓              |
| 177815                               | 31/2024/QH15         | Luật               |  2024 | dat_dai               |      0 |       0 |        0 |     0 |      0 |             0 | ✓               |                  0 |       0 |               0 |         0 |         0 |               0 |           0 |         0 |                  0 |                |
| 152668                               | 145/2020/NĐ-CP       | Nghị định          |  2020 | lao_dong              |   1740 |  244952 |       12 |    19 |    133 |           133 | ✗               |                 26 |     438 |               0 |       398 |         0 |              72 |         193 |         6 |                  0 | ✓              |
| 37590                                | 111/2013/TT-BTC      | Thông tư           |  2013 | thue_tncn             |   1142 |  177746 |        5 |     0 |     30 |            30 | ✓               |                  2 |     104 |               1 |       181 |         3 |              91 |          45 |         0 |                  0 | ✓              |
| 172779                               | 03/VBHN-VPQH         | Văn bản hợp nhất   |  2024 | thue_tncn             |      0 |       0 |        0 |     0 |      0 |             0 | ✓               |                  0 |       0 |               0 |         0 |         0 |               0 |           0 |         0 |                  0 |                |
| 44353                                | 117/2014/NĐ-CP       | Nghị định          |  2014 | bhyt                  |     58 |    6646 |        0 |     0 |      6 |             6 | ✓               |                  2 |      12 |               0 |        15 |         0 |               0 |           0 |         0 |                  0 | ✓              |
| 133859                               | 06/2019/NĐ-CP        | Nghị định          |  2019 | doanh_nghiep          |    413 |   62848 |        5 |     6 |     42 |            42 | ✓               |                  3 |     156 |               0 |       147 |         0 |               0 |           3 |         0 |                  0 | ✓              |
| 12161                                | 11/2009/TT-BLĐTBXH   | Thông tư           |  2009 | bhxh,lao_dong         |     58 |    7490 |        0 |     0 |      3 |             3 | ✓               |                  0 |      16 |               0 |         5 |         0 |               0 |           3 |         0 |                  0 | ✓              |
| 151000                               | 37/2021/TT-BTC       | Thông tư           |  2021 | doanh_nghiep          |     16 |    2571 |        0 |     0 |      2 |             2 | ✓               |                  1 |       2 |               0 |         0 |         0 |               0 |           3 |         0 |                  0 | ✓              |
| 122366                               | 02/2016/TTLT-BNG-BTP | Thông tư liên tịch |  2016 | hon_nhan_gia_dinh     |    194 |   32558 |        4 |     0 |     23 |            23 | ✓               |                  5 |      66 |               0 |        30 |         2 |              10 |           0 |         0 |                  0 | ✓              |
| 13411                                | 42/2007/NQ-CP        | Nghị quyết         |  2007 | dat_dai               |    304 |   19187 |        0 |     0 |      4 |             4 | ✓               |                  1 |      13 |               0 |         0 |         0 |               0 |         277 |         0 |                  0 |                |
| 24176                                | 39/2007/QĐ-BGTVT     | Quyết định         |  2007 | giao_thong_duong_bo   |     18 |    1793 |        0 |     0 |      3 |             3 | ✓               |                  3 |       0 |               0 |         0 |         0 |               3 |           0 |         0 |                  1 |                |
| 2f503350-6545-11f1-98c1-092062ae1bd4 | 02/VBHN-VPQH         | Văn bản hợp nhất   |  2026 | cu_tru                |    316 |   40652 |        6 |     6 |     59 |            59 | ✓               |                 30 |     115 |               0 |        66 |         0 |               0 |           2 |         0 |                  0 | ✓              |
| 179416                               | 81/2025/QH15         | Luật               |  2025 | hon_nhan_gia_dinh     |    381 |   53134 |        0 |     0 |     10 |            10 | ✗               |                  1 |     126 |               0 |       152 |         0 |               0 |           2 |         0 |                 50 | ✓              |
| 26167                                | 190/1999/QĐ-BLĐTBXH  | Quyết định         |  1999 | lao_dong              |    298 |   33527 |        0 |     0 |      3 |             3 | ✓               |                  2 |      20 |               0 |         0 |         0 |               0 |         260 |         0 |                  0 | ✓              |

Chú thích cột: `điều` = dòng khớp `^Điều N.`; `điều (lỏng)` = mọi dòng bắt đầu bằng "Điều N/thứ" (kể
cả `Điều 5:`); `điều không khoản` = điều không có dòng `^N. `; `dòng trích dẫn “` = dòng mở ngoặc
kép, thường là nội dung sửa đổi được trích lại trong văn bản sửa đổi/hợp nhất.

## 3. Trích đoạn

**139264** (từ dòng 8):

```text
Quốc hội ban hành Bộ luật Lao động.
Chương I
NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Bộ luật Lao động quy định tiêu chuẩn lao động; quyền, nghĩa vụ, trách nhiệm của người lao động, người sử dụng lao động, tổ chức đại diện người lao động tại cơ s
Điều 2. Đối tượng áp dụng
1. Người lao động, người học nghề, người tập nghề và người làm việc không có quan hệ lao động.
2. Người sử dụng lao động.
3. Người lao động nước ngoài làm việc tại Việt Nam.
4. Cơ quan, tổ chức, cá nhân khác có liên quan trực tiếp đến quan hệ lao động.
Điều 3. Giải thích từ ngữ
Trong Bộ luật này, các từ ngữ dưới đây được hiểu như sau:
1. Người lao động là người làm việc cho người sử dụng lao động theo thỏa thuận, được trả lương và chịu sự quản lý, điều hành, giám sát của người sử dụng lao độn
Độ tuổi lao động tối thiểu của người lao động là đủ 15 tuổi, trừ trường hợp quy định tại Mục 1 Chương XI của Bộ luật này.
2. Người sử dụng lao động là doanh nghiệp, cơ quan, tổ chức, hợp tác xã, hộ gia đình, cá nhân có thuê mướn, sử dụng người lao động làm việc cho mình theo thỏa t
3. Tổ chức đại diện người lao động tại cơ sở là tổ chức được thành lập trên cơ sở tự nguyện của người lao động tại một đơn vị sử dụng lao động nhằm mục đích bảo
4. Tổ chức đại diện người sử dụng lao động là tổ chức được thành lập hợp pháp, đại diện và bảo vệ quyền, lợi ích hợp pháp của người sử dụng lao động trong quan 
5. Quan hệ lao động là quan hệ xã hội phát sinh trong việc thuê mướn, sử dụng lao động, trả lương giữa người lao động, người sử dụng lao động, các tổ chức đại d
6. Người làm việc không có quan hệ lao động là người làm việc không trên cơ sở thuê mướn bằng hợp đồng lao động.
7. Cưỡng bức lao động là việc dùng vũ lực, đe dọa dùng vũ lực hoặc các thủ đoạn khác để ép buộc người lao động phải làm việc trái ý muốn của họ.
8. Phân biệt đối xử trong lao động là hành vi phân biệt, loại trừ hoặc ưu tiên dựa trên chủng tộc, màu da, nguồn gốc quốc gia hoặc nguồn gốc xã hội, dân tộc, gi
Việc phân biệt, loại trừ hoặc ưu tiên xuất phát từ yêu cầu đặc thù của công việc và các hành vi duy trì, bảo vệ việc làm cho người lao động dễ bị tổn thương thì
9. Quấy rối tình dục tại nơi làm việc là hành vi có tính chất tình dục của bất kỳ người nào đối với người khác tại nơi làm việc mà không được người đó mong muốn
Điều 4. Chính sách của Nhà nước về lao động
1. Bảo đảm quyền và lợi ích hợp pháp, chính đáng của người lao động, người làm việc không có quan hệ lao động; khuyến khích những thỏa thuận bảo đảm cho người l
```
**152668** (từ dòng 13):

```text
Chính phủ ban hành Nghị định quy định chi tiết và hướng dẫn thi hành một số điều của Bộ luật Lao động về điều kiện lao động và quan hệ lao động.
Chương I
NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Nghị định này quy định chi tiết và hướng dẫn thi hành một số nội dung về điều kiện lao động và quan hệ lao động theo các điều, khoản sau đây của Bộ luật Lao độn
1. Quản lý lao động theo khoản 3 Điều 12.
2. Hợp đồng lao động theo khoản 4 Điều 21; điểm d khoản 1 Điều 35, điểm d khoản 2 Điều 36; khoản 4 Điều 46; khoản 4 Điều 47; khoản 3 Điều 51.
3. Cho thuê lại lao động theo khoản 2 Điều 54.
4. Tổ chức đối thoại và thực hiện quy chế dân chủ ở cơ sở tại nơi làm việc theo khoản 4 Điều 63.
5. Tiền lương theo khoản 3 Điều 92; khoản 3 Điều 96; khoản 4 Điều 98.
6. Thời giờ làm việc, thời giờ nghỉ ngơi theo khoản 5 Điều 107, khoản 7 Điều 113, Điều 116.
7. Kỷ luật lao động, trách nhiệm vật chất theo khoản 5 Điều 118; khoản 6 Điều 122; khoản 2 Điều 130; Điều 131.
8. Lao động nữ và bảo đảm bình đẳng giới theo khoản 6 Điều 135.
9. Lao động là người giúp việc gia đình theo khoản 2 Điều 161.
10. Giải quyết tranh chấp lao động theo khoản 2 Điều 184; khoản 6 Điều 185; khoản 2 Điều 209; khoản 2 Điều 210.
Điều 2. Đối tượng áp dụng
1. Người lao động, người học nghề, tập nghề theo khoản 1 Điều 2 của Bộ luật Lao động.
2. Người sử dụng lao động theo khoản 2 Điều 2 của Bộ luật Lao động.
3. Các cơ quan, tổ chức, cá nhân khác có liên quan đến việc thực hiện quy định tại Nghị định này.
Chương II
QUẢN LÝ LAO ĐỘNG
Điều 3. Sổ quản lý lao động
Việc lập, cập nhật, quản lý, sử dụng sổ quản lý lao động tại khoản 1 Điều 12 của Bộ luật Lao động được quy định như sau:
1. Trong thời hạn 30 ngày kể từ ngày bắt đầu hoạt động, người sử dụng lao động phải lập sổ quản lý lao động ở nơi đặt trụ sở, chi nhánh, văn phòng đại diện.
2. Sổ quản lý lao động được lập bằng bản giấy hoặc bản điện tử nhưng phải bảo đảm các thông tin cơ bản về người lao động, gồm: họ tên; giới tính; ngày tháng năm
```
**37590** (từ dòng 19):

```text
Bộ trưởng Bộ Tài chính hướng dẫn thực hiện một số điều của Luật Thuế thu nhập cá nhân, Luật sửa đổi, bổ sung một số điều của Luật Thuế thu nhập cá nhân và Nghị 
Chương I
QUY ĐỊNH CHUNG
Điều 1. Người nộp thuế
Người nộp thuế là cá nhân cư trú và cá nhân không cư trú theo quy định tại Điều 2 Luật Thuế thu nhập cá nhân, Điều 2 Nghị định số 65/2013/NĐ-CP ngày 27/6/2013 c
Phạm vi xác định thu nhập chịu thuế của người nộp thuế như sau:
Đối với cá nhân cư trú, thu nhập chịu thuế là thu nhập phát sinh trong và ngoài lãnh thổ Việt Nam, không phân biệt nơi trả và nhận thu nhập.
Đối với cá nhân không cư trú, thu nhập chịu thuế là thu nhập phát sinh tại Việt Nam, không phân biệt nơi trả và nhận thu nhập.
1. Cá nhân cư trú là người đáp ứng một trong các điều kiện sau đây:
a) Có mặt tại Việt Nam từ 183 ngày trở lên tính trong một năm dương lịch hoặc trong 12 tháng liên tục kể từ ngày đầu tiên có mặt tại Việt Nam, trong đó ngày đến
Cá nhân có mặt tại Việt Nam theo hướng dẫn tại điểm này là sự hiện diện của cá nhân đó trên lãnh thổ Việt Nam.
b) Có nơi ở thường xuyên tại Việt Nam theo một trong hai trường hợp sau:
b.1) Có nơi ở thường xuyên theo quy định của pháp luật về cư trú:
b.1.1) Đối với công dân Việt Nam: nơi ở thường xuyên là nơi cá nhân sinh sống thường xuyên, ổn định không có thời hạn tại một chỗ ở nhất định và đã đăng ký thườ
b.1.2) Đối với người nước ngoài: nơi ở thường xuyên là nơi ở thường trú ghi trong Thẻ thường trú hoặc nơi ở tạm trú khi đăng ký cấp Thẻ tạm trú do cơ quan có th
b.2) Có nhà thuê để ở tại Việt Nam theo quy định của pháp luật về nhà ở, với thời hạn của các hợp đồng thuê từ 183 ngày trở lên trong năm tính thuế, cụ thể như 
b.2.1) Cá nhân chưa hoặc không có nơi ở thường xuyên theo hướng dẫn tại điểm b.1, khoản 1, Điều này nhưng có tổng số ngày thuê nhà để ở theo các hợp đồng thuê t
b.2.2) Nhà thuê để ở bao gồm cả trường hợp ở khách sạn, ở nhà khách, nhà nghỉ, nhà trọ, ở nơi làm việc, ở trụ sở cơ quan,... không phân biệt cá nhân tự thuê hay
Trường hợp cá nhân có nơi ở thường xuyên tại Việt Nam theo quy định tại khoản này nhưng thực tế có mặt tại Việt Nam dưới 183 ngày trong năm tính thuế mà cá nhân
Việc chứng minh là đối tượng cư trú của nước khác được căn cứ vào Giấy chứng nhận cư trú. Trường hợp cá nhân thuộc nước hoặc vùng lãnh thổ đã ký kết Hiệp định t
2. Cá nhân không cư trú là người không đáp ứng điều kiện nêu tại khoản 1, Điều này.
3. Người nộp thuế trong một số trường hợp cụ thể được xác định như sau:
a) Đối với cá nhân có thu nhập từ kinh doanh.
a.1) Trường hợp chỉ có một người đứng tên trong Giấy chứng nhận đăng ký kinh doanh thì người nộp thuế là cá nhân đứng tên trong Giấy chứng nhận đăng ký kinh doa
a.2) Trường hợp nhiều người cùng đứng tên trong Giấy chứng nhận đăng ký kinh doanh (nhóm cá nhân kinh doanh), cùng tham gia kinh doanh thì người nộp thuế là từn
```
**139264** — bảng:

```text
| QUỐC HỘI -------- | CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc --------------- |
| Bộ luật số: 45/2019/QH14 | Hà Nội, ngày 20 tháng 11 năm 2019 |
BỘ LUẬT
LAO ĐỘNG
Căn cứ Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam;
Quốc hội ban hành Bộ luật Lao động.
Chương I
NHỮNG QUY ĐỊNH CHUNG
```

## 4. Tỉ lệ toàn văn rỗng (trên 30,824 văn bản đã tải)

Tổng: 8.6% rỗng; văn bản trung ương có tính quy phạm:
9.3%.

### Theo loại

| loai_van_ban                 |     n | rỗng   |   median_ký_tự |
|:-----------------------------|------:|:-------|---------------:|
| Quyết định                   | 16013 | 7.5%   |         4551   |
| Nghị quyết                   |  4944 | 7.6%   |         4713.5 |
| Thông tư                     |  3335 | 5.8%   |        10322   |
| Chỉ thị                      |  1608 | 2.4%   |         5218   |
| Bản dịch văn bản             |  1330 | 5.0%   |         1571   |
| Nghị định                    |  1278 | 2.6%   |        17250   |
| Thông tư liên tịch           |   877 | 9.6%   |        10483   |
| Văn bản hợp nhất             |   553 | 90.8%  |        44404   |
| Sắc lệnh                     |   199 | 0.0%   |          925   |
| Luật                         |   196 | 4.6%   |        55805   |
| Công văn                     |   164 | 82.3%  |         2393   |
| Văn bản hệ thống hóa         |   108 | 0.0%   |        31191   |
| Văn bản hành chính liên quan |    63 | 3.2%   |         2703   |
| Pháp lệnh                    |    56 | 0.0%   |        13097   |
| Lệnh                         |    45 | 0.0%   |          617   |

### Theo giai đoạn ban hành (văn bản trung ương có tính quy phạm)

| giai đoạn   |    n | rỗng   |
|:------------|-----:|:-------|
| <2000       | 2042 | 9.1%   |
| 2000–09     | 3475 | 2.1%   |
| 2010–19     | 2514 | 10.4%  |
| 2020–22     |  578 | 24.6%  |
| 2023–24     |  400 | 23.2%  |
| 2025–26     |  612 | 19.1%  |

Trong số văn bản rỗng (trung ương, quy phạm), 7% có một bản ghi khác cùng số hiệu
và loại, có nội dung, trong cùng mẫu (vd 59/2020/QH14: id 142847 rỗng, id 142881 đủ).

## 5. Ước lượng theo lĩnh vực

Ước lượng = Σ (1 − tỉ lệ rỗng theo loại) × trung vị ký tự theo loại. Thô, chỉ để so sánh lĩnh vực.

| lĩnh vực            |   số văn bản |   trong mẫu row group | % rỗng (mẫu)   |   ước lượng văn bản có toàn văn |   ước lượng MB text |
|:--------------------|-------------:|----------------------:|:---------------|--------------------------------:|--------------------:|
| lao_dong            |          430 |                    96 | 2%             |                             397 |                 8.3 |
| dat_dai             |          535 |                   132 | 8%             |                             492 |                 8.3 |
| hon_nhan_gia_dinh   |           96 |                    20 | 15%            |                              81 |                 2   |
| thue_tncn           |           99 |                    24 | 38%            |                              73 |                 1.4 |
| giao_thong_duong_bo |          411 |                    75 | 4%             |                             369 |                 5.7 |
| bhxh                |          163 |                    49 | 2%             |                             149 |                 3.3 |
| doanh_nghiep        |          900 |                   184 | 15%            |                             790 |                13.6 |
| bhyt                |          109 |                    24 | 4%             |                              98 |                 1.9 |
| nha_o               |          157 |                    39 | 28%            |                             131 |                 2.7 |
| cu_tru              |           30 |                    10 | 0%             |                              28 |                 0.7 |

## 6. Bản crawl cũ (`legacy_content`)

`legacy/content.parquet` (plain text, 3,5 GB) chỉ có một row group, nên không đọc từng phần được.
Muốn dùng làm nguồn dự phòng cho văn bản rỗng thì phải tải trọn file; id của bản cũ khác hệ id
hiện tại, phải ghép theo số hiệu + loại + ngày ban hành.

# Kindle dash — kế hoạch đã chốt (26/11/2026)

Nhà duy nhất của luật dự án này. Bộ Não (`01_Tien_Do_Du_An.md` mục 3b) chỉ trỏ về đây.

## Máy móc
- Kindle Basic 3 (đời 10, 2019), màn dọc 600×800, 167ppi, xám 16 mức. Jailbreak + `kindle-dash` (KUAL): thức → Wi-Fi → tải PNG → hiện → ngủ.
- Mac + PC hay tắt → máy chủ là **GitHub Actions** của repo công khai này (miễn phí không giới hạn), cron 15 phút, vẽ PNG → GitHub Pages (đường dẫn khó đoán).
- Bí mật (link iCal bí mật, token đọc `Lam_AI_Brain`, Google Tasks) chỉ nằm trong Actions secrets. Repo không chứa dữ liệu cá nhân.
- Mac/PC khi mở phiên Claude: hook đẩy `usage.json` (chỉ con số, token Claude không rời máy). Cũng giữ repo "có hoạt động" để GitHub không tắt cron.
- Chạy ổn định: **0 token AI**.

## Màn ban ngày (07h–00h), 1 trang, tiếng Việt
Giao diện: **mẫu A đã chốt 26/11** (`mau/mau.html`, ảnh `mau/mau-a.png`): ngày + thời tiết trên cùng; 2 thẻ Claude / Antigravity tên đậm; lịch + việc chữ 19px, kẻ mảnh giữa việc, không ký hiệu lịch; chân trang "Cập nhật · Pin". Nhiều sự kiện quá thì cắt + "+N sự kiện nữa" để không tràn.
1. **Hạn mức** (trên cùng), 2 thẻ riêng cùng kiểu: **Claude** và **Antigravity**, mỗi thẻ 2 ô số to % **đã dùng** 5 giờ + tuần + "làm mới lúc HH:MM". ≥ 80% → nền đen "sắp hết". Số cũ > 3 giờ → mờ + "số cũ".
   - Claude: thanh trạng thái Claude Code (`rate_limits`) ghi ra file, không đọc token.
   - Antigravity: máy chủ cục bộ của app (`RetrieveUserQuotaSummary`, chỉ khi app mở), lấy nhóm dùng nhiều nhất, không ghi tên model. Hỏng thì ẩn ô.
2. **Lịch**: ~3 ngày, tối đa 6 dòng, ưu tiên ngày gần, tràn thì "+N sự kiện nữa". Lịch: chính + Work + Study + Ngày lễ (ký hiệu nhỏ). Chỉ giờ + tiêu đề, không mô tả/link/người.
3. **Todo list** (tối đa 5 dòng): 3 việc ★ từ mục `## Việc ngắn` của `01_Tien_Do_Du_An.md` (không có ★ thì 3 việc hạn gần nhất) + 2 việc Google Tasks mặc định (ẩn việc xong). Nhãn dự án `[BCTT]` `[Video]` `[Tài chính]` `[Não]` `[Kindle]`, dự án mới cùng kiểu. Việc sắp đến hạn luôn xếp đầu ("còn N ngày"). Việc Bộ Não không bao giờ "trễ": qua hạn tự ẩn; không hạn thì tự ẩn sau 7 ngày kể từ ngày ghi (dòng có `+dd/mm`); AI đầu phiên hỏi gọn việc ★ cũ "xong chưa?". Chỉ Google Tasks quá hạn mới nền đen.
   - **Trùng Bộ Não ↔ Tasks** (so tên đã bỏ dấu, nhãn, ngày; giống ≥ 60% từ): gộp thành 1 dòng, dùng chữ + nhãn + hạn của Bộ Não.
   - **Tích xong trên Google Tasks** → Kindle ẩn ngay việc Bộ Não trùng; lần mở phiên AI tới, script đầu phiên xóa dòng đó khỏi `## Việc ngắn` (0 token). AI xóa việc trong Bộ Não → tích xong việc Tasks trùng (web app cần quyền sửa Tasks).
   - Sự kiện lặp ("Đi làm") vẫn hiện bình thường.
- Ô phụ: thứ + ngày (không âm lịch), thời tiết TP.HCM (Open-Meteo: nhiệt độ + khả năng mưa), pin Kindle, giờ cập nhật. Không hiện giờ phút hiện tại.

## Màn ban đêm (00h–07h)
"Ngủ ngon" + mèo nằm ngủ trên bệ cửa sổ, ánh trăng phía sau (nét đơn giản, hợp e-ink) + lịch và việc chính ngày mai. Kindle ngủ tới 7h.

## Màn khóa (bấm nút nguồn tắt màn hình) = ảnh đang hiện
Ban ngày bấm tắt → giữ nguyên dashboard đang hiện; 00h–07h → màn đêm mèo ngủ. Cách làm: mỗi lần tải ảnh, Kindle chép đúng `dash.png` vừa hiện vào thư mục màn chờ của ScreenSavers hack (KUAL, GĐ 5) — 5.17+ cần thêm bước, 5.18 chưa ai xác nhận → đối chiếu đúng firmware; không được thì Kindle giữ màn khóa mặc định.
- Pin: ảnh vẽ trên đám mây không biết pin Kindle → góc phải chân trang để trống, script trên Kindle tự in "Pin NN%".

## Giai đoạn
1. Mẫu giao diện (Claude) → Lâm chọn · 2. Script vẽ ảnh (Anti viết, Claude kiểm) · 3. Actions + Pages (Anti, Claude kiểm bảo mật) · 4. Hook số Claude + thử đo Antigravity (Claude) · 5. Jailbreak + cài (Lâm bấm, Claude chỉ) · 6. Hướng dẫn xử lý lỗi (Anti, Claude duyệt).

# Kindle dash — kế hoạch đã chốt (26/11/2026)

Nhà duy nhất của luật dự án này. Bộ Não (`01_Tien_Do_Du_An.md` mục 3b) chỉ trỏ về đây.

## Máy móc
- Kindle Basic 3 (đời 10, 2019), màn dọc 600×800, 167ppi, xám 16 mức. Jailbreak + `kindle-dash` (KUAL): thức → Wi-Fi → tải PNG → hiện → ngủ.
- Mac + PC hay tắt → máy chủ là **GitHub Actions** của repo công khai này (miễn phí không giới hạn), cron 15 phút, vẽ PNG → GitHub Pages (đường dẫn khó đoán).
- Bí mật (link iCal bí mật, token đọc `Lam_AI_Brain`, Google Tasks) chỉ nằm trong Actions secrets. Repo không chứa dữ liệu cá nhân.
- Mac/PC khi mở phiên Claude: hook đẩy `usage.json` (chỉ con số, token Claude không rời máy). Cũng giữ repo "có hoạt động" để GitHub không tắt cron.
- Chạy ổn định: **0 token AI**.

## Màn ban ngày (07h–00h), 1 trang, tiếng Việt
1. **Hạn mức** (trên cùng), 2 dòng cùng kiểu: **Claude** và **Antigravity**, mỗi dòng % **đã dùng** 5 giờ + tuần + "làm mới lúc HH:MM". ≥ 80% → nền đen "sắp hết". Số cũ > 3 giờ → mờ + "số cũ".
   - Claude: thanh trạng thái Claude Code (`rate_limits`) ghi ra file, không đọc token.
   - Antigravity: máy chủ cục bộ của app (`RetrieveUserQuotaSummary`, chỉ khi app mở), lấy nhóm dùng nhiều nhất, không ghi tên model. Hỏng thì ẩn ô.
2. **Sự kiện sắp tới**: ~3 ngày, tối đa 6 dòng, ưu tiên ngày gần, tràn thì "+N sự kiện nữa". Lịch: chính + Work + Study + Ngày lễ (ký hiệu nhỏ). Chỉ giờ + tiêu đề, không mô tả/link/người.
3. **Việc** (tối đa 5 dòng): 3 việc ★ từ mục `## Việc ngắn` của `01_Tien_Do_Du_An.md` (không có ★ thì 3 việc hạn gần nhất) + 2 việc Google Tasks mặc định (ẩn việc xong). Nhãn dự án `[BCTT]` `[Video]` `[Tài chính]` `[Não]` `[Kindle]`, dự án mới cùng kiểu. Việc sắp đến hạn luôn xếp đầu ("còn N ngày"). Việc Bộ Não không bao giờ "trễ": qua hạn tự ẩn; không hạn thì tự ẩn sau 7 ngày kể từ ngày ghi (dòng có `+dd/mm`); AI đầu phiên hỏi gọn việc ★ cũ "xong chưa?". Chỉ Google Tasks quá hạn mới nền đen.
- Ô phụ: thứ + ngày (không âm lịch), thời tiết TP.HCM (Open-Meteo: nhiệt độ + khả năng mưa), pin Kindle, giờ cập nhật. Không hiện giờ phút hiện tại.

## Màn ban đêm (00h–07h)
"Ngủ ngon" + mèo nằm ngủ trên bệ cửa sổ, ánh trăng phía sau (nét đơn giản, hợp e-ink) + lịch và việc chính ngày mai. Kindle ngủ tới 7h.

## Giai đoạn
1. Mẫu giao diện (Claude) → Lâm chọn · 2. Script vẽ ảnh (Anti viết, Claude kiểm) · 3. Actions + Pages (Anti, Claude kiểm bảo mật) · 4. Hook số Claude + thử đo Antigravity (Claude) · 5. Jailbreak + cài (Lâm bấm, Claude chỉ) · 6. Hướng dẫn xử lý lỗi (Anti, Claude duyệt).

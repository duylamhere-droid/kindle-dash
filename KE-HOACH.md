# Kindle dash — kiến trúc hiện tại (v3, 27/11/2026)

Nhà duy nhất của luật dự án này. Bộ Não (`01_Tien_Do_Du_An.md` mục 3b) chỉ trỏ về đây.

## Máy móc & vận hành
- **Kindle Paperwhite 3** (đời 7, 2015), firmware 5.16.2.1.1, màn dọc `1072×1448`, 300ppi, xám 16 mức. Ảnh vẽ bố cục 600 CSS px rồi chụp ×1,786 (`ve/ve.py`).
- **Jailbreak:** WinterBreak + `kindle-dash` (`dash.sh` / `fetch-dashboard.sh` trên Kindle):
  - **Ban ngày (07:00–23:00):** tự tính lịch thức các mốc `:03 / :18 / :33 / :48`, bật Wi-Fi tải `dash.png` từ GitHub Pages → hiện → ngủ sâu tới mốc kế tiếp.
  - **Ban đêm (23:00–07:00):** hiện `sleeping.png` (mèo ngủ) và ngủ liền tới `07:03`.
- **Máy chủ vẽ ảnh:** GitHub Actions (`.github/workflows/ve-anh.yml`, miễn phí) chạy mỗi 15 phút hoặc khi `so/` thay đổi → vẽ `ra/dash.png` → đăng lên GitHub Pages (thư mục bí mật `PAGES_DIR`).
- **Đẩy số từ Mac & PC (`may/day_so.py`):** chạy định kỳ 15 phút (`launchd` `com.lam.kindle-dash` trên Mac, Task Scheduler trên PC theo `may/CAI-PC.md`).
  - **Claude:** đọc OAuth token từ Keychain (Mac) hoặc `~/.claude/.credentials.json` (PC) → hỏi `api.anthropic.com/api/oauth/usage`. Khi token sắp/đã hết hạn → tự đổi qua `refresh_token` (`platform.claude.com/v1/oauth/token`, 0 tốn token chat) và lưu lại.
  - **Antigravity:** hỏi máy chủ cục bộ `hub_*.json` (`RetrieveUserQuotaSummary`, chỉ khi app đang mở), lấy nhóm dùng nhiều nhất.
  - Chỉ đẩy `so/claude.json` và `so/antigravity.json` lên repo khi số đổi hoặc đã quá 2 giờ; nếu số không đổi trong giờ thức (7h–23h) thì gọi `gh workflow run ve-anh.yml` giữ nhịp 15 phút.
  - Token không bao giờ rời máy; trên repo chỉ có phần trăm + giờ làm mới.

## Giao diện v3 (`ve/ve.py`)
1. **Tiêu đề:** Thứ + ngày bên trái, đồng hồ 24h bên phải (`28px`).
2. **2 khung hạn mức (Claude & Antigravity):** Phiên 5 giờ + Tuần này (% đã dùng, thanh tiến độ, giờ/ngày làm mới). `≥ 80%` → nền đen "sắp hết". Số cũ `> 3 giờ` → mờ + "số cũ".
3. **Khung mèo (`ve/meo/`):** 5 biểu cảm chọn theo **Claude · Phiên 5 giờ** + câu thoại chữa lành xoay vòng mỗi 15 phút (`hoi`, `gian`, `toi`, `ban`, `tim`).
4. **Ban đêm (`23:00–07:00`):** màn ngủ "Ngủ ngon~" với `ve/meo/ngu.png`.

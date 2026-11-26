# Cài đẩy số trên PC (Windows) — cho AI trên PC làm theo

Mac đã cài (launchd `com.lam.kindle-dash`, 15 phút). PC làm tương tự để khi chỉ mở PC, số vẫn lên Kindle.

1. Cần: Python 3, `gh` đã đăng nhập tài khoản `duylamhere-droid` (`gh auth status`), repo `kindle-dash` đã kéo về (vd `F:\Documents\AI\Projects\kindle-dash`).
2. Chạy thử: `python may\day_so.py` → thấy `✓ antigravity.json` khi Antigravity đang mở.
3. Lên lịch 15 phút (PowerShell, đổi đường dẫn cho đúng):
   ```powershell
   schtasks /Create /TN "kindle-dash" /SC MINUTE /MO 15 /TR "python F:\Documents\AI\Projects\kindle-dash\may\day_so.py" /F
   ```
4. Số Claude trên PC: script đọc `%USERPROFILE%\.claude\.credentials.json` (có khi đã đăng nhập `claude` trong Terminal).
5. Gỡ: `schtasks /Delete /TN "kindle-dash" /F`.

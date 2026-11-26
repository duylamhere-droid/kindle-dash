# Cài đẩy số trên PC (Windows) — cho AI trên PC làm theo

Mac đã cài (launchd `com.lam.kindle-dash`, 15 phút). PC làm tương tự để khi chỉ mở PC, số vẫn lên Kindle.

1. Cần: Python 3, `gh` đã đăng nhập tài khoản `duylamhere-droid` (`gh auth status`), repo `kindle-dash` đã kéo về (vd `F:\Documents\AI\Projects\kindle-dash`).
2. Chạy thử: `python may\day_so.py` → thấy `✓ antigravity.json` khi Antigravity đang mở.
3. Lên lịch 15 phút (PowerShell; `schtasks` vỡ với đường dẫn có emoji nên dùng `Register-ScheduledTask`; `pythonw -X utf8` = không hiện cửa sổ, không lỗi chữ):
   ```powershell
   $py = (Get-Command pythonw).Source; $d = "F:\Documents\AI\Projects\📟 Kindle dash"
   $a = New-ScheduledTaskAction -Execute $py -Argument "-X utf8 `"$d\may\day_so.py`"" -WorkingDirectory $d
   $t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15)
   $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
   Register-ScheduledTask -TaskName "kindle-dash" -Action $a -Trigger $t -Settings $s -Force
   ```
4. Số Claude trên PC: script đọc `%USERPROFILE%\.claude\.credentials.json` (có khi đã đăng nhập `claude` trong Terminal).
5. Gỡ: `Unregister-ScheduledTask kindle-dash -Confirm:$false`.
6. PC đã cài 26/11 (thư mục `F:\Documents\AI\Projects\📟 Kindle dash`). PowerShell cũ có thể không thấy `claude` → gọi `%APPDATA%\npm\claude.cmd auth login`.

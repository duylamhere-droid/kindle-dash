"""Thanh trạng thái Claude Code: nhận số hạn mức Claude Code gửi sẵn (rate_limits), ghi ra ~/.kindle-dash/claude.json.
Không đọc token. Chạy được trên Mac và PC (chỉ thư viện chuẩn)."""
import json, sys, time
from pathlib import Path

d = json.load(sys.stdin)
out = Path.home() / ".kindle-dash"
out.mkdir(exist_ok=True)
rl = d.get("rate_limits") or {}
if rl:
    (out / "claude.json").write_text(json.dumps({"rate_limits": rl, "luc": int(time.time())}))
# shortcut: ghi tên trường để kiểm lần đầu, xóa khi đã chắc dữ liệu ổn định
(out / "statusline-keys.json").write_text(json.dumps(sorted(d.keys())))

p = lambda k: round((rl.get(k) or {}).get("used_percentage") or 0)
print(f"Claude 5h {p('five_hour')}% · tuần {p('seven_day')}%" if rl else "Claude · chưa có số hạn mức")

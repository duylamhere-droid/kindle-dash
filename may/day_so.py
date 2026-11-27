"""Đẩy số hạn mức Claude + Antigravity của máy này lên repo kindle-dash (thư mục so/). Mac + PC, thư viện chuẩn + gh.
Chạy định kỳ 15 phút (launchd trên Mac, Task Scheduler trên PC). Lâm chọn 26/11: đọc token Claude Code trong Keychain.

- Token chỉ dùng để hỏi api.anthropic.com, KHÔNG ghi ra file, KHÔNG in ra, KHÔNG đẩy lên. Lên repo chỉ có con số + giờ.
- Nguồn nào lỗi (app tắt, token hết hạn) thì bỏ qua nguồn đó; Kindle tự hiện "số cũ".
- Chỉ đẩy khi số đổi hoặc đã quá 2 giờ (để số không bị coi là cũ), tránh spam commit.
"""
import base64, getpass, glob, json, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

REPO = "duylamhere-droid/kindle-dash"
NHA = Path.home() / ".kindle-dash"
DAY_LAI_SAU = 2 * 3600
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
_CREDS_FILE = Path.home() / ".claude" / ".credentials.json"


def _doc_claude_creds():
    if sys.platform == "darwin":
        r = subprocess.run(["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                           capture_output=True, text=True)
        raw = r.stdout if r.returncode == 0 else ""
    else:  # Windows/Linux: Claude Code cất trong file
        raw = _CREDS_FILE.read_text(encoding="utf-8") if _CREDS_FILE.is_file() else ""
    try:
        return json.loads(raw)
    except Exception:
        return None


def _luu_claude_creds(full):
    noi_dung = json.dumps(full)
    if sys.platform == "darwin":
        subprocess.run(
            ["security", "add-generic-password", "-U", "-a", getpass.getuser(),
             "-s", "Claude Code-credentials", "-w", noi_dung],
            capture_output=True, text=True,
        )
    elif _CREDS_FILE.parent.is_dir():
        _CREDS_FILE.write_text(noi_dung, encoding="utf-8")


def _lam_moi_token_claude():
    full = _doc_claude_creds()
    oauth = (full or {}).get("claudeAiOauth") or {}
    rt = oauth.get("refreshToken")
    if not rt:
        return False
    req = urllib.request.Request(
        "https://platform.claude.com/v1/oauth/token",
        data=json.dumps({"grant_type": "refresh_token", "refresh_token": rt, "client_id": CLAUDE_CLIENT_ID}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "claude-code/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.load(r)
        if not res.get("access_token"):
            return False
        oauth["accessToken"] = res["access_token"]
        if res.get("refresh_token"):
            oauth["refreshToken"] = res["refresh_token"]
        if res.get("expires_in"):
            oauth["expiresAt"] = int((time.time() + res["expires_in"]) * 1000)
        if res.get("refresh_token_expires_in"):
            oauth["refreshTokenExpiresAt"] = int((time.time() + res["refresh_token_expires_in"]) * 1000)
        _luu_claude_creds(full)
        return True
    except Exception:
        return False


def token_claude():
    full = _doc_claude_creds()
    try:
        return full["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


_NO_WIN = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


def _epoch(v):
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str) and v:
        from datetime import datetime
        return int(datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp())
    return None


def so_claude():
    tk = token_claude()
    if not tk:  # chưa đăng nhập Claude Code trong Terminal → dùng số thanh trạng thái (may/statusline.py) nếu có
        f = NHA / "claude.json"
        return {"rate_limits": json.loads(f.read_text())["rate_limits"]} if f.is_file() else None
    req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
        "Authorization": "Bearer " + tk, "anthropic-beta": "oauth-2025-04-20", "User-Agent": "kindle-dash"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401 and not getattr(so_claude, "da_thu", False):
            # Token 8 giờ hết hạn: tự đổi accessToken mới qua OAuth refresh_token (0 tốn token) rồi thử lại 1 lần.
            so_claude.da_thu = True
            if _lam_moi_token_claude():
                return so_claude()
        print("✗ claude: HTTP", e.code); return None
    except Exception as e:
        print("✗ claude:", type(e).__name__); return None
    rl = {}
    for k in ("five_hour", "seven_day"):
        w = d.get(k) or {}
        pct = w.get("utilization", w.get("used_percentage"))
        if pct is not None:
            rl[k] = {"used_percentage": float(pct), "resets_at": _epoch(w.get("resets_at"))}
    if not rl:
        print("✗ claude: không thấy five_hour/seven_day, khóa nhận được:", sorted(d.keys())); return None
    return {"rate_limits": rl}


def so_antigravity():
    for f in sorted(glob.glob(str(Path.home() / ".gemini/antigravity/daemon/hub_*.json"))):
        try:
            d = json.load(open(f))
            req = urllib.request.Request(
                f"http://127.0.0.1:{d['httpPort']}/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary",
                data=b"{}", headers={"Content-Type": "application/json", "X-Codeium-Csrf-Token": d["csrfToken"],
                                     "Connect-Protocol-Version": "1"})
            with urllib.request.urlopen(req, timeout=8) as r:
                j = json.load(r)
            groups = [{"displayName": g.get("displayName"),
                       "buckets": [{k: b.get(k) for k in ("window", "remainingFraction", "resetTime")} for b in g.get("buckets", [])]}
                      for g in j["response"]["groups"]]
            return {"response": {"groups": groups}}
        except Exception:
            continue  # app tắt hoặc file hub cũ
    return None


def day(ten, du_lieu, cache):
    """Ghi so/<ten> lên GitHub bằng gh api (không cần clone repo). Trả về True nếu có đẩy."""
    khoa = json.dumps(du_lieu, sort_keys=True)
    cu = cache.get(ten, {})
    if cu.get("khoa") == khoa and time.time() - cu.get("luc", 0) < DAY_LAI_SAU:
        print("= ", ten, "không đổi"); return False
    du_lieu = dict(du_lieu, luc=int(time.time()))
    path = f"repos/{REPO}/contents/so/{ten}"
    sha = subprocess.run(["gh", "api", path, "--jq", ".sha"], capture_output=True, text=True, **_NO_WIN).stdout.strip()
    noi_dung = base64.b64encode(json.dumps(du_lieu).encode()).decode()
    args = ["gh", "api", "-X", "PUT", path, "-f", f"message=so: {ten}", "-f", f"content={noi_dung}", "--silent"]
    if sha:
        args += ["-f", f"sha={sha}"]
    if subprocess.run(args, **_NO_WIN).returncode == 0:
        cache[ten] = {"khoa": khoa, "luc": time.time()}; print("✓", ten); return True
    print("✗ đẩy", ten); return False


def main():
    if sys.stdout: sys.stdout.reconfigure(encoding="utf-8")  # console Windows cp1252 không in được tiếng Việt
    NHA.mkdir(exist_ok=True)
    cf = NHA / "da-day.json"
    cache = json.loads(cf.read_text()) if cf.is_file() else {}
    da_day = False
    for ten, ham in (("claude.json", so_claude), ("antigravity.json", so_antigravity)):
        d = ham()
        if d and day(ten, d, cache):
            da_day = True
    cf.write_text(json.dumps(cache))
    # GitHub Actions cron hay trễ/bỏ lượt: nếu số không đổi trong giờ thức (7h-23h), gọi vẽ ảnh trực tiếp
    if not da_day and 7 <= time.localtime().tm_hour < 23:
        subprocess.run(["gh", "workflow", "run", "ve-anh.yml", "-R", REPO], capture_output=True, **_NO_WIN)


if __name__ == "__main__":
    main()

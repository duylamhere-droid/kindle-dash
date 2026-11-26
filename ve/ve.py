"""Vẽ màn hình Kindle 1072x1448 (PW3) (HTML + PNG xám 16 mức) từ dữ liệu JSON."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from html import escape
import json
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

VN = ZoneInfo("Asia/Ho_Chi_Minh")
THU_DAY = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
THU_NGAN = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
CHROME_MAC = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TIEN_TO_TASK = 'Added a new reminder to my list: "'


def doc_du_lieu(thu_muc: str | Path) -> dict:
    """Đọc các file JSON trong thư mục; thiếu file thì bỏ qua khóa đó."""
    goc = Path(thu_muc)
    kq: dict = {}
    for khoa, ten in [
        ("google", "google.json"),
        ("claude", "claude.json"),
        ("antigravity", "antigravity.json"),
    ]:
        duong = goc / ten
        if duong.is_file():
            try:
                kq[khoa] = json.loads(duong.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
    return kq


def lam_sach_task(s: str) -> str:
    """Bỏ tiền tố nhắc việc của Google Assistant và dấu ngoặc kép cuối."""
    s = s.strip()
    if s.startswith(TIEN_TO_TASK):
        s = s[len(TIEN_TO_TASK):]
        if s.endswith('"'):
            s = s[:-1]
    return s.strip()


def _sang_vn(bay_gio: datetime) -> datetime:
    if bay_gio.tzinfo is None:
        return bay_gio.replace(tzinfo=VN)
    return bay_gio.astimezone(VN)


def _doc_gio(val: str | int | float | None) -> datetime | None:
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=VN)
    s = str(val).strip()
    if not s:
        return None
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return datetime.fromisoformat(s).replace(tzinfo=VN)
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=VN)
    return dt.astimezone(VN)


def _dinh_dang_han_muc(
    pct: int, reset_dt: datetime | None, bay_gio: datetime, cu: bool
) -> tuple[bool, str]:
    canh_bao = pct >= 80
    parts: list[str] = []
    if canh_bao:
        parts.append("sắp hết")
    if reset_dt is not None:
        if reset_dt.date() == bay_gio.date():
            parts.append(f"làm mới lúc {reset_dt:%H:%M}")
        else:
            parts.append(f"làm mới {THU_NGAN[reset_dt.weekday()]} {reset_dt:%d/%m}")
    if cu:
        parts.append("số cũ")
    return canh_bao, " · ".join(parts)


def _tinh_han_muc(du_lieu: dict, bay_gio: datetime) -> list[dict]:
    kq: list[dict] = []

    claude = du_lieu.get("claude")
    if isinstance(claude, dict) and isinstance(claude.get("rate_limits"), dict):
        rl = claude["rate_limits"]
        luc = _doc_gio(claude.get("luc"))
        cu = bool(luc and (bay_gio - luc).total_seconds() > 3 * 3600)
        o: list[dict] = []
        for khoa, nhan in (("five_hour", "Phiên 5 giờ"), ("seven_day", "Tuần này")):
            muc = rl.get(khoa) or {}
            pct = max(0, min(100, round(float(muc.get("used_percentage", 0)))))
            reset_dt = _doc_gio(muc.get("resets_at"))
            canh_bao, phu = _dinh_dang_han_muc(pct, reset_dt, bay_gio, cu)
            o.append({"nhan": nhan, "pct": pct, "canh_bao": canh_bao, "phu": phu})
        kq.append({"ten": "Claude", "co_so": True, "cu": cu, "o": o})
    else:
        kq.append({"ten": "Claude", "co_so": False, "cu": False, "o": []})

    ag = du_lieu.get("antigravity")
    groups = ((ag or {}).get("response") or {}).get("groups") if isinstance(ag, dict) else None
    if isinstance(groups, list) and groups:
        luc = _doc_gio(ag.get("luc"))
        cu = bool(luc and (bay_gio - luc).total_seconds() > 3 * 3600)

        def _tach_nhom(g: dict) -> tuple[float, dict[str, dict]]:
            theo_win: dict[str, dict] = {}
            max_used = -1.0
            for b in g.get("buckets") or []:
                win = b.get("window")
                if win in ("5h", "weekly"):
                    rem = b.get("remainingFraction")
                    if rem is None:
                        rem = 1.0
                    used = max(0.0, min(1.0, 1.0 - float(rem)))
                    theo_win[win] = {"used": used, "reset": _doc_gio(b.get("resetTime"))}
                    if used > max_used:
                        max_used = used
            return max_used, theo_win

        _, chon = max((_tach_nhom(g) for g in groups), key=lambda x: x[0])
        o = []
        for win, nhan in (("5h", "Phiên 5 giờ"), ("weekly", "Tuần này")):
            muc = chon.get(win, {"used": 0.0, "reset": None})
            pct = max(0, min(100, round(muc["used"] * 100)))
            canh_bao, phu = _dinh_dang_han_muc(pct, muc["reset"], bay_gio, cu)
            o.append({"nhan": nhan, "pct": pct, "canh_bao": canh_bao, "phu": phu})
        kq.append({"ten": "Antigravity", "co_so": True, "cu": cu, "o": o})
    else:
        kq.append({"ten": "Antigravity", "co_so": False, "cu": False, "o": []})

    return kq


def _tinh_su_kien(du_lieu: dict, bay_gio: datetime) -> list[dict]:
    google = du_lieu.get("google")
    su_kien_raw = (google or {}).get("su_kien") if isinstance(google, dict) else []
    if not isinstance(su_kien_raw, list):
        su_kien_raw = []

    hom_nay = bay_gio.date()
    bon_ngay = [hom_nay + timedelta(days=i) for i in range(4)]
    gom: dict[date, list[tuple[int, datetime, str, str]]] = {d: [] for d in bon_ngay}

    for ev in su_kien_raw:
        bd = _doc_gio(ev.get("bat_dau"))
        kt = _doc_gio(ev.get("ket_thuc"))
        if bd is None:
            continue
        if kt is not None and kt <= bay_gio:
            continue
        ca_ngay = bool(ev.get("ca_ngay"))
        tieu_de = str(ev.get("tieu_de", "")).strip()
        if ca_ngay:
            ngay_bd = bd.date()
            ngay_kt = (kt - timedelta(seconds=1)).date() if kt is not None else ngay_bd
            for d in bon_ngay:
                if ngay_bd <= d <= ngay_kt:
                    gom[d].append((0, bd, "Cả ngày", tieu_de))
        else:
            d = bd.date()
            if d in gom:
                gom[d].append((1, bd, f"{bd:%H:%M}", tieu_de))

    kq: list[dict] = []
    for i, d in enumerate(bon_ngay):
        nhan = "Hôm nay" if i == 0 else f"{THU_DAY[d.weekday()]} {d:%d/%m}"
        gom[d].sort(key=lambda x: (x[0], x[1]))
        dong = [{"gio": gio, "tieu_de": td} for _, _, gio, td in gom[d]]
        kq.append({"nhan": nhan, "dong": dong})
    return kq


def _chu_han(han_ngay: date | None, hom_nay: date) -> tuple[str, bool]:
    if han_ngay is None:
        return "", False
    diff = (han_ngay - hom_nay).days
    if diff < 0:
        return f"trễ {-diff} ngày", True
    if diff == 0:
        return "hôm nay", False
    return f"còn {diff} ngày", False


def _tinh_viec(du_lieu: dict, bay_gio: datetime, che_do: str) -> list[dict]:
    """Lấy danh sách Todo duy nhất từ Google Tasks (việc có hạn xếp trước)."""
    hom_nay = bay_gio.date()
    google = du_lieu.get("google") or {}
    viec_gg_raw = google.get("viec") if isinstance(google, dict) else []
    if not isinstance(viec_gg_raw, list):
        return []

    ds: list[tuple[bool, date, int, dict]] = []
    for idx, g in enumerate(viec_gg_raw):
        chu = lam_sach_task(str(g.get("tieu_de", "")))
        if not chu:
            continue
        han_raw = g.get("han")
        han_ngay = date.fromisoformat(str(han_raw)[:10]) if han_raw else None
        han_str, tre = _chu_han(han_ngay, hom_nay)
        ds.append((han_ngay is None, han_ngay or date.max, idx, {"chu": chu, "han": han_str, "tre": tre}))

    ds.sort(key=lambda item: (item[0], item[1], item[2]))
    gioi_han = 3 if che_do == "dem" else 5
    return [item[3] for item in ds[:gioi_han]]


def tinh(du_lieu: dict, bay_gio: datetime) -> dict:
    """Biến đổi dữ liệu thô thành mô hình hiển thị cho ban ngày hoặc ban đêm."""
    bg = _sang_vn(bay_gio)
    che_do = "dem" if 0 <= bg.hour < 7 else "ngay"
    thu = THU_DAY[bg.weekday()]
    ngay_str = f"{bg:%d/%m}"
    ngay_tieu_de = f"Mai là {thu}, {ngay_str}" if che_do == "dem" else f"{thu}, {ngay_str}"

    return {
        "che_do": che_do,
        "ngay_tieu_de": ngay_tieu_de,
        "gio_24": f"{bg:%H:%M}",
        "cap_nhat": f"{bg:%H:%M}",
        "han_muc": _tinh_han_muc(du_lieu, bg),
        "su_kien": _tinh_su_kien(du_lieu, bg),
        "viec": _tinh_viec(du_lieu, bg, che_do),
    }


def _ve_html_ngay(m: dict) -> str:
    the_hm = []
    for hm in m["han_muc"]:
        cls = "card ai cu" if hm["cu"] else "card ai"
        if hm["co_so"]:
            o_html = "".join(
                f'<div class="u{" warn" if o["canh_bao"] else ""}">'
                f'<div class="name">{escape(o["nhan"])}</div>'
                f'<div class="pct">{o["pct"]}<small>%</small></div>'
                f'<div class="bar"><i style="width:{o["pct"]}%"></i></div>'
                f'<div class="sub">{escape(o["phu"])}</div>'
                f"</div>"
                for o in hm["o"]
            )
            noi_dung = f'<div class="usage">{o_html}</div>'
        else:
            noi_dung = '<div class="usage"><div class="u"><div class="sub">chưa có số</div></div></div>'
        the_hm.append(f'<div class="{cls}">\n  <div class="brand">{escape(hm["ten"])}</div>\n  {noi_dung}\n</div>')

    su_kien_html: list[str] = []
    for i, d in enumerate(m["su_kien"]):
        if i == 0 and not d["dong"]:
            su_kien_html.append(f'  <div class="day">{escape(d["nhan"])}</div>')
            su_kien_html.append('  <div class="ev none">— Không có sự kiện</div>')
        elif d["dong"]:
            su_kien_html.append(f'  <div class="day">{escape(d["nhan"])}</div>')
            for ev in d["dong"]:
                su_kien_html.append(
                    f'  <div class="ev"><span class="t">{escape(ev["gio"])}</span>'
                    f'<span>{escape(ev["tieu_de"])}</span></div>'
                )

    viec_html: list[str] = []
    for v in m["viec"]:
        cls = "todo late" if v["tre"] else "todo"
        han = f'<span class="due">{escape(v["han"])}</span>' if v["han"] else ""
        viec_html.append(
            f'  <div class="{cls}"><span class="s">○</span>'
            f'<span class="txt">{escape(v["chu"])}</span>{han}</div>'
        )
    if not viec_html:
        viec_html.append('  <div class="ev none">— Không có việc nào</div>')

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=block" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:600px;height:810px;overflow:hidden;background:#fff;color:#000}}
body{{font-family:"Be Vietnam Pro",sans-serif;font-size:15px;line-height:1.25;padding:16px 26px 0;position:relative}}
.head{{display:flex;justify-content:space-between;align-items:center;padding-bottom:10px;border-bottom:1.5px solid #000;margin-bottom:2px}}
.date,.clock{{font-size:28px;font-weight:800;letter-spacing:-.6px;line-height:1}}
.clock{{font-variant-numeric:tabular-nums}}
.card{{border:1.8px solid #222;border-radius:14px;padding:10px 16px;margin-top:9px}}
.card.ai{{border:2.5px solid #000;border-radius:16px;padding:14px 18px 15px;margin-top:11px}}
.card.cu{{opacity:.45}}
.label{{font-size:11px;font-weight:800;letter-spacing:1.6px;text-transform:uppercase;color:#555;margin-bottom:5px}}
.brand{{font-size:22px;font-weight:800;letter-spacing:-.4px;line-height:1.05;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #d4d4d4}}
.usage{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.u{{padding:2px 0}}
.u .name{{font-size:14.5px;font-weight:600;color:#444;margin-bottom:4px}}
.u .pct{{font-size:56px;font-weight:800;line-height:.95;letter-spacing:-2.5px;font-variant-numeric:tabular-nums}}
.u .pct small{{font-size:26px;letter-spacing:0;font-weight:700;margin-left:1px}}
.bar{{height:14px;border:2px solid #000;border-radius:999px;margin-top:9px;position:relative;overflow:hidden}}
.bar i{{position:absolute;inset:0 auto 0 0;background:#000}}
.u .sub{{font-size:13px;font-weight:500;color:#555;margin-top:6px}}
.u.warn{{background:#000;color:#fff;padding:8px 12px 9px;margin:-6px -8px;border-radius:11px}}
.u.warn .name,.u.warn .sub{{color:#d8d8d8}}
.u.warn .bar{{border-color:#fff}}.u.warn .bar i{{background:#fff}}
.lich-card{{font-size:13.5px;padding:9px 16px}}
.lich-card .day{{font-size:12px;font-weight:700;color:#555;margin:5px 0 1px}}
.lich-card .day:first-of-type{{margin-top:0}}
.ev{{display:flex;gap:10px;padding:1.5px 0}}
.ev .t{{min-width:54px;flex:none;font-weight:700;white-space:nowrap}}
.ev.none{{color:#666;font-style:italic}}
.more{{font-size:12px;color:#555;padding:3px 0 0}}
.todo-card{{font-size:15px;padding:9px 16px}}
.todo{{display:flex;align-items:baseline;gap:8px;padding:4px 0}}
.todo+.todo{{border-top:1px solid #dcdcdc}}
.todo .s{{width:14px;flex:none;font-weight:700;color:#444}}
.todo .txt{{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.todo .due{{font-size:12.5px;font-weight:700;white-space:nowrap}}
.todo.late{{background:#000;color:#fff;padding:4px 9px;margin:0 -9px 2px;border-radius:8px}}
.todo.late .s{{color:#fff}}
.todo.late+.todo{{border-top:none}}
.foot{{position:absolute;left:26px;right:26px;bottom:8px;display:flex;justify-content:space-between;font-size:12px;color:#555;border-top:1px solid #999;padding-top:4px}}
</style>
</head>
<body>
<div class="head"><div class="date">{escape(m["ngay_tieu_de"])}</div><div class="clock">{escape(m["gio_24"])}</div></div>

{chr(10).join(the_hm)}

<div class="card lich-card" id="lich">
  <div class="label">Lịch</div>
{chr(10).join(su_kien_html)}
</div>

<div class="card todo-card" id="viec">
  <div class="label">Todo list</div>
{chr(10).join(viec_html)}
</div>

<div class="foot"><span>Cập nhật {escape(m["cap_nhat"])}</span><span id="pin"></span></div>
<script>
(function(){{
  var lich=document.getElementById("lich"),viec=document.getElementById("viec");
  if(!lich||!viec)return;
  function tran(){{return viec.getBoundingClientRect().bottom>810-34;}}
  var cut=0,more=document.createElement("div");
  more.className="more";
  if(tran()){{
    lich.appendChild(more);
    while(tran()){{
      var evs=lich.querySelectorAll(".ev:not(.none)");
      if(!evs.length)break;
      evs[evs.length-1].remove();
      cut++;
      while(more.previousElementSibling&&more.previousElementSibling.classList.contains("day")){{
        more.previousElementSibling.remove();
      }}
      more.textContent="+"+cut+" sự kiện nữa";
    }}
  }}
  var r=viec.getBoundingClientRect(),du=810-34-r.bottom;
  if(du>0)viec.style.minHeight=(r.height+du)+"px";
}})();
</script>
</body>
</html>"""


def _ve_html_dem(m: dict) -> str:
    dong_su_kien = (m["su_kien"][0]["dong"] if m["su_kien"] else [])
    if dong_su_kien:
        lich_html = "\n".join(
            f'  <div class="row ev"><b>{escape(ev["gio"])}</b><span>{escape(ev["tieu_de"])}</span></div>'
            for ev in dong_su_kien
        )
    else:
        lich_html = '  <div class="row none"><span>— Không có sự kiện</span></div>'

    if m["viec"]:
        viec_html = "\n".join(
            f'  <div class="row"><span>○ {escape(v["chu"])}</span>'
            f'{f"""<span class="due">{escape(v["han"])}</span>""" if v["han"] else ""}</div>'
            for v in m["viec"]
        )
    else:
        viec_html = '  <div class="row none"><span>— Không có việc nào</span></div>'

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;700;800&display=block" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:600px;height:810px;overflow:hidden;background:#fff;color:#000}}
body{{font-family:"Be Vietnam Pro",sans-serif;font-size:19px;line-height:1.28;position:relative}}
svg{{display:block;margin-bottom:-18px}}
.txt{{padding:0 40px}}
h1{{font-size:44px;font-weight:800;letter-spacing:-1px;margin-top:0}}
.sub{{font-size:18px;color:#444;margin-top:2px}}
.label{{font-size:15px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#555;margin:14px 0 4px}}
.row{{display:flex;gap:12px;padding:4px 0;border-bottom:1px solid #ccc}}
.row b{{min-width:62px;flex:none;white-space:nowrap}}
.row.none{{color:#666;font-style:italic}}
.more{{font-size:15px;color:#555;padding:3px 0}}
.row .due{{margin-left:auto;font-size:15px;font-weight:700;white-space:nowrap}}
.foot{{position:absolute;left:40px;right:40px;bottom:14px;display:flex;justify-content:space-between;font-size:14px;color:#555}}
</style>
</head>
<body>
<svg width="600" height="420" viewBox="0 0 600 420">
  <rect x="60" y="30" width="480" height="330" fill="#222"/>
  <rect x="78" y="48" width="444" height="294" fill="#3a3a3a"/>
  <circle cx="390" cy="150" r="92" fill="#4a4a4a"/>
  <circle cx="390" cy="150" r="62" fill="#e8e8e8"/>
  <circle cx="370" cy="135" r="10" fill="#d0d0d0"/>
  <circle cx="408" cy="168" r="7" fill="#d0d0d0"/>
  <g fill="#bbb"><circle cx="140" cy="90" r="2.5"/><circle cx="200" cy="150" r="2"/><circle cx="480" cy="80" r="2.5"/><circle cx="250" cy="70" r="1.8"/><circle cx="490" cy="250" r="2"/><circle cx="130" cy="230" r="1.8"/></g>
  <rect x="294" y="48" width="12" height="294" fill="#222"/>
  <rect x="78" y="190" width="444" height="10" fill="#222"/>
  <rect x="30" y="342" width="540" height="26" rx="4" fill="#888"/>
  <rect x="30" y="368" width="540" height="10" fill="#555"/>
  <g fill="#fff" stroke="#000" stroke-width="5" stroke-linejoin="round" stroke-linecap="round">
    <path d="M150 342 C150 278 210 252 268 256 C330 260 372 292 372 342 Z"/>
    <path d="M330 342 C318 300 340 276 372 274 C404 272 428 296 424 342 Z"/>
    <path d="M350 286 L356 254 L374 276"/>
    <path d="M396 276 L414 256 L416 290"/>
  </g>
  <path d="M160 340 C120 344 112 372 128 392 C138 404 156 400 152 388" fill="none" stroke="#000" stroke-width="10" stroke-linecap="round"/>
  <path d="M160 340 C120 344 112 372 128 392 C138 404 156 400 152 388" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
  <g fill="none" stroke="#000" stroke-width="3.5" stroke-linecap="round">
    <path d="M358 312 q8 6 16 0"/><path d="M390 312 q8 6 16 0"/>
  </g>
  <path d="M378 324 l4 4 l4 -4 z" fill="#000"/>
  <g fill="none" stroke="#000" stroke-width="4" stroke-linecap="round">
    <path d="M220 268 q8 14 2 28"/><path d="M250 260 q8 16 2 32"/><path d="M282 262 q6 14 0 28"/>
  </g>
  <g font-family="Be Vietnam Pro" font-weight="800" fill="#fff"><text x="440" y="262" font-size="26">z</text><text x="466" y="236" font-size="20">z</text><text x="486" y="216" font-size="15">z</text></g>
</svg>

<div class="txt" id="txt">
  <h1>Ngủ ngon</h1>
  <div class="sub">{escape(m["ngay_tieu_de"])}</div>

  <div class="label">Lịch ngày mai</div>
  <div id="lich-dem">
{lich_html}
  </div>

  <div class="label">Todo list</div>
{viec_html}
</div>

<div class="foot"><span>Dậy lúc 07:00</span><span id="pin"></span></div>
<script>
(function(){{
  var txt=document.getElementById("txt"),lich=document.getElementById("lich-dem");
  if(!txt||!lich)return;
  function tran(){{return txt.getBoundingClientRect().bottom>810-40;}}
  if(!tran())return;
  var cut=0,more=document.createElement("div");
  more.className="more";
  lich.appendChild(more);
  while(tran()){{
    var evs=lich.querySelectorAll(".ev");
    if(!evs.length)break;
    evs[evs.length-1].remove();
    cut++;
    more.textContent="+"+cut+" sự kiện nữa";
  }}
}})();
</script>
</body>
</html>"""


def ve_html(mo_hinh: dict) -> str:
    """Dựng chuỗi HTML 1072x1448 (PW3) hoàn chỉnh từ mô hình đã tính."""
    if mo_hinh.get("che_do") == "dem":
        return _ve_html_dem(mo_hinh)
    return _ve_html_ngay(mo_hinh)


def _tim_chrome() -> str:
    env = os.environ.get("CHROME")
    if env:
        return env
    if Path(CHROME_MAC).exists():
        return CHROME_MAC
    return "google-chrome"


def chup(html_path: str | Path, png_path: str | Path) -> None:
    """Chụp HTML 1072x1448 (PW3) bằng Chrome headless và đổi sang PNG xám 16 mức."""
    from PIL import Image

    html_abs = Path(html_path).resolve()
    png_abs = Path(png_path).resolve()
    png_abs.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _tim_chrome(),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1.786667",  # Paperwhite 3: 1072x1448, giữ bố cục 600 CSS px
        "--window-size=600,810",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        f"--screenshot={png_abs}",
        html_abs.as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with Image.open(png_abs) as img:
        xam = img.convert("L").resize((1072, 1448)).quantize(16).convert("L")
        xam.save(png_abs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vẽ ảnh Kindle 1072x1448 (PW3) từ dữ liệu JSON.")
    parser.add_argument("--du-lieu", required=True, help="Thư mục dữ liệu đầu vào")
    parser.add_argument("--ra", required=True, help="Thư mục xuất dash.html và dash.png")
    parser.add_argument("--gio", help="Thời điểm giả lập ISO (YYYY-MM-DDTHH:MM), mặc định giờ VN hiện tại")
    args = parser.parse_args()

    bay_gio = _doc_gio(args.gio) if args.gio else datetime.now(VN)
    du_lieu = doc_du_lieu(args.du_lieu)
    mo_hinh = tinh(du_lieu, bay_gio)
    html = ve_html(mo_hinh)

    ra = Path(args.ra)
    ra.mkdir(parents=True, exist_ok=True)
    html_path = ra / "dash.html"
    png_path = ra / "dash.png"
    html_path.write_text(html, encoding="utf-8")
    chup(html_path, png_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

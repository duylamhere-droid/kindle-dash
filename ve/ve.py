"""Vẽ màn hình Kindle 1072x1448 (PW3) (HTML + PNG xám 16 mức) từ dữ liệu JSON."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
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
MEO_DIR = Path(__file__).parent / "meo"

# Câu thoại ngọt ngào chữa lành theo trạng thái Claude · Phiên 5 giờ (xoay vòng mỗi 15 phút)
CAU_MEO = {
    "hoi": [
        "Ủa... chưa thấy số mới đâu cả~",
        "Đợi xíu nha, đang ngóng số từ máy tính nè~",
    ],
    "gian": [
        "Claude sắp cạn rồi~ nghỉ tay xíu cho đỡ mệt nha!",
        "Tém tém lại chút thôi~ chờ hồi lực rồi làm tiếp nhé!",
        "Hôm nay làm cháy quá rồi~ thả lỏng vai xíu nào!",
    ],
    "toi": [
        "Tối rồi đó~ hôm nay làm tốt lắm rồi, nghỉ sớm nha ♡",
        "Để phần còn lại cho ngày mai cũng không sao đâu~",
        "Sắp tới giờ đi ngủ rồi~ khép máy sớm cho khỏe nhé!",
    ],
    "ban": [
        "Uống ngụm nước, giãn vai xíu rồi làm tiếp nha~",
        "Đừng quên chớp mắt và thở sâu một nhịp nhé~",
        "Đi được nửa chặng rồi~ cứ đều tay là đẹp nha!",
    ],
    "tim": [
        "Hôm nay nhẹ nhàng thôi~ cứ từ từ mà làm nhé ♡",
        "Còn dư dả lắm~ làm chậm mà chắc nha!",
        "Chúc một ngày thật êm~ không bug không deadline gắt ♡",
    ],
}


def doc_du_lieu(thu_muc: str | Path) -> dict:
    """Đọc các file JSON trong thư mục; thiếu file thì bỏ qua khóa đó."""
    goc = Path(thu_muc)
    kq: dict = {}
    for khoa, ten in (("claude", "claude.json"), ("antigravity", "antigravity.json")):
        duong = goc / ten
        if duong.is_file():
            try:
                kq[khoa] = json.loads(duong.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
    return kq


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
        if reset_dt.date() == bay_gio.date() or 0 <= (reset_dt - bay_gio).total_seconds() < 12 * 3600:
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


def _tinh_meo(han_muc: list[dict], bay_gio: datetime) -> dict:
    """Chọn biểu cảm mèo + câu thoại dựa duy nhất vào Claude · Phiên 5 giờ và giờ trong ngày."""
    claude = han_muc[0] if han_muc else {"co_so": False, "cu": False, "o": []}
    if not claude.get("co_so") or claude.get("cu"):
        loai = "hoi"
    else:
        pct_5h = claude["o"][0]["pct"] if claude.get("o") else 0
        if pct_5h >= 80:
            loai = "gian"
        elif 21 <= bay_gio.hour < 23:
            loai = "toi"
        elif pct_5h >= 50:
            loai = "ban"
        else:
            loai = "tim"

    ds_cau = CAU_MEO[loai]
    # Xoay vòng câu mỗi 15 phút để mỗi lượt cập nhật đều mới mẻ
    slot = (bay_gio.toordinal() * 96 + bay_gio.hour * 4 + bay_gio.minute // 15) % len(ds_cau)
    return {"loai": loai, "cau": ds_cau[slot]}


def _anh_meo_b64(ten: str) -> str:
    p = MEO_DIR / f"{ten}.png"
    if not p.is_file():
        return ""
    return base64.b64encode(p.read_bytes()).decode("ascii")


def tinh(du_lieu: dict, bay_gio: datetime) -> dict:
    """Biến đổi dữ liệu thô thành mô hình hiển thị cho ban ngày hoặc ban đêm."""
    bg = _sang_vn(bay_gio)
    che_do = "dem" if (bg.hour >= 23 or bg.hour < 7) else "ngay"
    thu = THU_DAY[bg.weekday()]
    ngay_str = f"{bg:%d/%m}"
    ngay_tieu_de = f"Ngủ ngon · {thu}, {ngay_str}" if che_do == "dem" else f"{thu}, {ngay_str}"
    han_muc = _tinh_han_muc(du_lieu, bg)

    return {
        "che_do": che_do,
        "ngay_tieu_de": ngay_tieu_de,
        "gio_24": f"{bg:%H:%M}",
        "cap_nhat": f"{bg:%H:%M}",
        "han_muc": han_muc,
        "meo": _tinh_meo(han_muc, bg),
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

    meo = m["meo"]
    b64 = _anh_meo_b64(meo["loai"])
    img_tag = f'<img class="cat-img" src="data:image/png;base64,{b64}" alt="{escape(meo["loai"])}">' if b64 else ""

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
.card.ai{{border:2.5px solid #000;border-radius:16px;padding:14px 18px 15px;margin-top:11px}}
.card.cu{{opacity:.45}}
.brand{{font-size:22px;font-weight:800;letter-spacing:-.4px;line-height:1.05;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #d4d4d4}}
.usage{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.u{{padding:2px 0}}
.u .name{{font-size:14.5px;font-weight:600;color:#444;margin-bottom:4px}}
.u .pct{{font-size:58px;font-weight:800;line-height:.95;letter-spacing:-2.5px;font-variant-numeric:tabular-nums}}
.u .pct small{{font-size:26px;letter-spacing:0;font-weight:700;margin-left:1px}}
.bar{{height:14px;border:2px solid #000;border-radius:999px;margin-top:9px;position:relative;overflow:hidden}}
.bar i{{position:absolute;inset:0 auto 0 0;background:#000}}
.u .sub{{font-size:13px;font-weight:500;color:#555;margin-top:6px}}
.u.warn{{background:#000;color:#fff;padding:8px 12px 9px;margin:-6px -8px;border-radius:11px}}
.u.warn .name,.u.warn .sub{{color:#d8d8d8}}
.u.warn .bar{{border-color:#fff}}.u.warn .bar i{{background:#fff}}
.cat-box{{
  margin-top:11px;
  height:282px;
  border:1.8px solid #222;
  border-radius:16px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  padding:14px 24px 12px;
  gap:14px;
}}
.bubble{{
  position:relative;
  background:#fff;
  border:2px solid #000;
  border-radius:18px;
  padding:11px 20px;
  font-size:17.5px;
  font-weight:600;
  line-height:1.35;
  text-align:center;
  max-width:480px;
}}
.bubble:after{{
  content:"";
  position:absolute;
  bottom:-10px;
  left:50%;
  transform:translateX(-50%) rotate(45deg);
  width:16px;
  height:16px;
  background:#fff;
  border-right:2px solid #000;
  border-bottom:2px solid #000;
}}
.cat-img{{
  max-height:168px;
  max-width:250px;
  object-fit:contain;
  display:block;
}}
.foot{{position:absolute;left:26px;right:26px;bottom:8px;display:flex;justify-content:space-between;font-size:12px;color:#555;border-top:1px solid #999;padding-top:4px}}
</style>
</head>
<body>
<div class="head"><div class="date">{escape(m["ngay_tieu_de"])}</div><div class="clock">{escape(m["gio_24"])}</div></div>

{chr(10).join(the_hm)}

<div class="cat-box">
  <div class="bubble">{escape(meo["cau"])}</div>
  {img_tag}
</div>

<div class="foot"><span>Cập nhật {escape(m["cap_nhat"])}</span><span id="pin"></span></div>
</body>
</html>"""


def _ve_html_dem(m: dict) -> str:
    b64 = _anh_meo_b64("ngu") or _anh_meo_b64("toi")
    img_tag = f'<img class="sleep-cat" src="data:image/png;base64,{b64}" alt="sleeping">' if b64 else ""

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&display=block" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:600px;height:810px;overflow:hidden;background:#fff;color:#000}}
body{{font-family:"Be Vietnam Pro",sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 36px 56px;text-align:center;position:relative}}
.sleep-cat{{width:360px;height:360px;object-fit:contain;margin-bottom:22px}}
h1{{font-size:48px;font-weight:800;letter-spacing:-1px;line-height:1.1}}
.sub{{font-size:19px;font-weight:600;color:#444;margin-top:12px;line-height:1.4}}
.foot{{position:absolute;left:36px;right:36px;bottom:16px;display:flex;justify-content:space-between;font-size:13px;color:#555;border-top:1px solid #bbb;padding-top:6px}}
</style>
</head>
<body>
  {img_tag}
  <h1>Ngủ ngon~</h1>
  <div class="sub">Hôm nay làm tốt lắm rồi ♡<br>Hẹn gặp lại lúc 07:00 sáng mai nhé</div>
  <div class="foot"><span>Chế độ nghỉ đêm (23:00 – 07:00)</span><span id="pin"></span></div>
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

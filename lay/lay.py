"""Gom dữ liệu cho ve.py vào 1 thư mục. Chạy trên GitHub Actions (hoặc Mac để thử).
Nguồn nào lỗi thì bỏ qua nguồn đó (ve.py tự hiện "chưa có số"/trống), không làm hỏng cả lượt.
Không in URL/token ra log: lỗi chỉ in tên loại lỗi.

Biến môi trường: GAS_URL, GAS_TOKEN (web app lịch + Tasks), BRAIN_FILE (01_Tien_Do_Du_An.md), SO_DIR (thư mục so/ chứa claude.json, antigravity.json do Mac/PC đẩy lên).
"""
import json, os, shutil, sys, time, urllib.parse, urllib.request
from pathlib import Path

THOI_TIET = ("https://api.open-meteo.com/v1/forecast?latitude=10.82&longitude=106.63"
             "&current=temperature_2m&daily=temperature_2m_max,precipitation_probability_max"
             "&timezone=Asia%2FHo_Chi_Minh&forecast_days=3")


def lay_json(url, lan=3):
    for i in range(lan):  # mạng chập chờn: thử lại, cách 5 giây
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if i == lan - 1:
                raise
            time.sleep(5)


def ghi(ra, ten, du_lieu):
    (ra / ten).write_text(json.dumps(du_lieu, ensure_ascii=False), encoding="utf-8")
    print("✓", ten)


def main(ra):
    ra.mkdir(parents=True, exist_ok=True)

    url, token = os.environ.get("GAS_URL"), os.environ.get("GAS_TOKEN")
    if url and token:
        try:
            g = lay_json(url + "?" + urllib.parse.urlencode({"token": token}))
            if "loi" in g:
                print("✗ google.json: web app từ chối (sai token?)")
            else:
                ghi(ra, "google.json", g)
        except Exception as e:
            print("✗ google.json:", type(e).__name__)

    try:
        ghi(ra, "thoi-tiet.json", lay_json(THOI_TIET))
    except Exception as e:
        print("✗ thoi-tiet.json:", type(e).__name__)

    brain = os.environ.get("BRAIN_FILE")
    if brain and Path(brain).is_file():
        shutil.copy(brain, ra / "viec-ngan.md"); print("✓ viec-ngan.md")
    else:
        print("✗ viec-ngan.md: không thấy file Bộ Não")

    so = Path(os.environ.get("SO_DIR", "so"))
    for ten in ("claude.json", "antigravity.json"):
        if (so / ten).is_file():
            shutil.copy(so / ten, ra / ten); print("✓", ten)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "du-lieu"))

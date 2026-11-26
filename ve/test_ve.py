"""Bài kiểm cho ve.py. Chạy: python -m unittest discover -s ve -q"""
import sys, unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import ve  # noqa: E402

VN = ZoneInfo("Asia/Ho_Chi_Minh")
MAU = Path(__file__).parent.parent / "du-lieu-mau"


def luc(s):
    return datetime.fromisoformat(s).replace(tzinfo=VN)


def du_lieu_claude(pct_5h, luc_ts=None):
    return {
        "claude": {
            "rate_limits": {
                "five_hour": {"used_percentage": pct_5h, "resets_at": None},
                "seven_day": {"used_percentage": 90, "resets_at": None},
            },
            "luc": luc_ts,
        }
    }


class TestNgay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-26T14:10"))

    def test_che_do_va_tieu_de(self):
        self.assertEqual(self.m["che_do"], "ngay")
        self.assertEqual(self.m["ngay_tieu_de"], "Thứ Năm, 26/11")
        self.assertEqual(self.m["gio_24"], "14:10")
        self.assertEqual(self.m["cap_nhat"], "14:10")

    def test_han_muc_claude(self):
        c = self.m["han_muc"][0]
        self.assertEqual(c["ten"], "Claude")
        self.assertTrue(c["co_so"]); self.assertFalse(c["cu"])
        o5, ot = c["o"]
        self.assertEqual((o5["nhan"], o5["pct"], o5["canh_bao"], o5["phu"]), ("Phiên 5 giờ", 34, False, "làm mới lúc 15:40"))
        self.assertEqual((ot["nhan"], ot["pct"], ot["canh_bao"], ot["phu"]), ("Tuần này", 86, True, "sắp hết · làm mới T3 01/12"))

    def test_han_muc_antigravity_nhom_dung_nhieu_nhat(self):
        a = self.m["han_muc"][1]
        self.assertEqual(a["ten"], "Antigravity")
        o5, ot = a["o"]
        self.assertEqual((o5["pct"], o5["phu"]), (23, "làm mới lúc 14:43"))
        self.assertEqual((ot["pct"], ot["phu"]), (18, "làm mới T3 01/12"))

    def test_meo_theo_claude_5h(self):
        # Du lieu mau co Claude 5h = 34% (du tuan = 86%) -> meo tim
        self.assertEqual(self.m["meo"]["loai"], "tim")
        self.assertEqual(ve.tinh(du_lieu_claude(62), luc("2026-11-26T14:10"))["meo"]["loai"], "ban")
        self.assertEqual(ve.tinh(du_lieu_claude(85), luc("2026-11-26T14:10"))["meo"]["loai"], "gian")
        # 21h-22h59 va 5h < 80% -> meo toi; neu 5h >= 80% -> van meo gian
        self.assertEqual(ve.tinh(du_lieu_claude(30), luc("2026-11-26T21:30"))["meo"]["loai"], "toi")
        self.assertEqual(ve.tinh(du_lieu_claude(85), luc("2026-11-26T21:30"))["meo"]["loai"], "gian")


class TestKhac(unittest.TestCase):
    def test_so_cu_hon_3_gio_ra_meo_hoi(self):
        m = ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-26T18:00"))
        self.assertTrue(m["han_muc"][0]["cu"])
        self.assertEqual(m["meo"]["loai"], "hoi")

    def test_thieu_file_claude_ra_meo_hoi(self):
        d = ve.doc_du_lieu(MAU); d.pop("claude", None)
        m = ve.tinh(d, luc("2026-11-26T14:10"))
        self.assertFalse(m["han_muc"][0]["co_so"])
        self.assertEqual(m["meo"]["loai"], "hoi")

    def test_ban_dem_23h_den_7h(self):
        self.assertEqual(ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-26T23:00"))["che_do"], "dem")
        self.assertEqual(ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-27T01:00"))["che_do"], "dem")
        self.assertEqual(ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-27T07:00"))["che_do"], "ngay")

    def test_reset_qua_nua_dem_van_hien_gio(self):
        _, phu = ve._dinh_dang_han_muc(10, luc("2026-11-27T02:02"), luc("2026-11-26T22:41"), False)
        self.assertEqual(phu, "làm mới lúc 02:02")

    def test_html_co_dong_ho_va_meo(self):
        h = ve.ve_html(ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-26T14:10")))
        for chu in ["Claude", "Antigravity", "14:10", "Cập nhật 14:10", "cat-box", "bubble"]:
            self.assertIn(chu, h)
        self.assertNotIn("Todo list", h)
        self.assertNotIn("mưa", h)


if __name__ == "__main__":
    unittest.main()

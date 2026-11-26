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

    def test_su_kien_4_ngay_bo_viec_da_qua(self):
        ngay = self.m["su_kien"]
        self.assertEqual([d["nhan"] for d in ngay], ["Hôm nay", "Thứ Sáu 27/11", "Thứ Bảy 28/11", "Chủ Nhật 29/11"])
        self.assertEqual([(x["gio"], x["tieu_de"]) for x in ngay[0]["dong"]], [("16:00", "Gọi khách hàng")])
        self.assertEqual([(x["gio"], x["tieu_de"]) for x in ngay[1]["dong"]],
                         [("Cả ngày", "Ngày lễ mẫu"), ("08:30", "Đi làm"), ("20:00", "Meet sửa bài - Thực Tập TTĐPT")])
        self.assertEqual([(x["gio"], x["tieu_de"]) for x in ngay[2]["dong"]], [("09:00", "Quay vlog")])

    def test_viec_chi_tu_google_tasks(self):
        v = self.m["viec"]
        self.assertEqual(v[0]["chu"], "Gửi hóa đơn anh Hoàng")
        self.assertEqual((v[0]["tre"], v[0]["han"]), (True, "trễ 1 ngày"))
        self.assertIn("Mua mực máy in", [x["chu"] for x in v])
        self.assertNotIn("Gửi firmware + cắm USB", [x["chu"] for x in v])  # không lấy từ Bộ Não
        self.assertLessEqual(len(v), 5)


class TestKhac(unittest.TestCase):
    def test_so_cu_hon_3_gio(self):
        m = ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-26T18:00"))
        self.assertTrue(m["han_muc"][0]["cu"])

    def test_thieu_file_claude(self):
        d = ve.doc_du_lieu(MAU); d.pop("claude", None)
        m = ve.tinh(d, luc("2026-11-26T14:10"))
        self.assertFalse(m["han_muc"][0]["co_so"])

    def test_ban_dem(self):
        m = ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-27T01:00"))
        self.assertEqual(m["che_do"], "dem")
        self.assertEqual(m["ngay_tieu_de"], "Mai là Thứ Sáu, 27/11")
        self.assertEqual([x["tieu_de"] for x in m["su_kien"][0]["dong"]],
                         ["Ngày lễ mẫu", "Đi làm", "Meet sửa bài - Thực Tập TTĐPT"])
        self.assertLessEqual(len(m["viec"]), 3)

    def test_7h_la_ban_ngay(self):
        self.assertEqual(ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-27T07:00"))["che_do"], "ngay")

    def test_reset_qua_nua_dem_van_hien_gio(self):
        _, phu = ve._dinh_dang_han_muc(10, luc("2026-11-27T02:02"), luc("2026-11-26T22:41"), False)
        self.assertEqual(phu, "làm mới lúc 02:02")

    def test_lam_sach_task(self):
        self.assertEqual(ve.lam_sach_task('Added a new reminder to my list: "ôn apt"'), "ôn apt")
        self.assertEqual(ve.lam_sach_task("Mua mực"), "Mua mực")

    def test_html_co_dong_ho_khong_thoi_tiet(self):
        h = ve.ve_html(ve.tinh(ve.doc_du_lieu(MAU), luc("2026-11-26T14:10")))
        for chu in ["Claude", "Antigravity", "Lịch", "Todo list", "14:10", "Cập nhật 14:10", "trễ 1 ngày"]:
            self.assertIn(chu, h)
        self.assertNotIn("mưa", h)
        self.assertNotIn("class=\"tag\"", h)


if __name__ == "__main__":
    unittest.main()

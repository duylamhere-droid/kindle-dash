// Web app chỉ-đọc cho Kindle dash: trả lịch 3 ngày tới + Google Tasks dạng JSON.
// Cần ?token= khớp TOKEN trong bimat.js (file này không lên GitHub, chỉ đẩy lên Apps Script bằng clasp).
// Chỉ trả giờ + tiêu đề: không mô tả, link, người tham gia.

const LICH = ['Work', 'Study', 'Ngày lễ ở Việt Nam']; // cộng lịch chính
const KY_HIEU = { 'Work': 'W', 'Study': 'S', 'Ngày lễ ở Việt Nam': 'L' };

function doGet(e) {
  if (!e || !e.parameter || e.parameter.token !== TOKEN) return json_({ loi: 'sai token' });
  if (e.parameter.xong) return json_(tichXong_(e.parameter.xong));
  return json_({ luc: new Date().toISOString(), su_kien: suKien_(), viec: viec_(), xong_gan_day: xongGanDay_() });
}

function suKien_() {
  const tu = new Date(), den = new Date(tu.getTime() + 4 * 864e5); // dư 1 ngày, phía vẽ tự cắt 3 ngày
  const lichs = [CalendarApp.getDefaultCalendar()].concat(
    CalendarApp.getAllCalendars().filter(c => LICH.indexOf(c.getName()) >= 0));
  const ra = [];
  lichs.forEach(c => c.getEvents(tu, den).forEach(ev => ra.push({
    bat_dau: ev.getStartTime().toISOString(),
    ket_thuc: ev.getEndTime().toISOString(),
    ca_ngay: ev.isAllDayEvent(),
    tieu_de: ev.getTitle(),
    lich: KY_HIEU[c.getName()] || ''
  })));
  return ra.sort((a, b) => a.bat_dau < b.bat_dau ? -1 : 1);
}

function dsMacDinh_() {
  const ds = Tasks.Tasklists.list({ maxResults: 1 }).items || []; // danh sách mặc định = đầu tiên
  return ds.length ? ds[0].id : null;
}

function viec_() {
  const id = dsMacDinh_(); if (!id) return [];
  const items = Tasks.Tasks.list(id, { showCompleted: false, maxResults: 50 }).items || [];
  return items.filter(t => t.title).map(t => ({ id: t.id, tieu_de: t.title, han: t.due || null }));
}

// Việc tích xong 14 ngày qua: Kindle ẩn việc Bộ Não trùng, script đầu phiên xóa dòng Bộ Não.
function xongGanDay_() {
  const id = dsMacDinh_(); if (!id) return [];
  const tu = new Date(Date.now() - 14 * 864e5).toISOString();
  const items = Tasks.Tasks.list(id, { showCompleted: true, showHidden: true, completedMin: tu, maxResults: 100 }).items || [];
  return items.filter(t => t.status === 'completed' && t.title).map(t => ({ id: t.id, tieu_de: t.title, luc: t.completed }));
}

// Chỉ đổi trạng thái thành "xong", không sửa/xóa gì khác.
function tichXong_(taskId) {
  const id = dsMacDinh_(); if (!id) return { loi: 'không có danh sách' };
  try { Tasks.Tasks.patch({ status: 'completed' }, id, taskId); return { ok: true }; }
  catch (err) { return { loi: String(err) }; }
}

// Chạy 1 lần trong trình soạn Apps Script để cấp quyền đọc Lịch + Tasks; in số lượng để kiểm.
function capQuyen() {
  Logger.log('Sự kiện: ' + suKien_().length + ' · Việc: ' + viec_().length);
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

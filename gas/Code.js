// Web app chỉ-đọc cho Kindle dash: trả lịch 3 ngày tới + Google Tasks dạng JSON.
// Cần ?token= khớp TOKEN trong bimat.js (file này không lên GitHub, chỉ đẩy lên Apps Script bằng clasp).
// Chỉ trả giờ + tiêu đề: không mô tả, link, người tham gia.

const LICH = ['Work', 'Study', 'Ngày lễ ở Việt Nam']; // cộng lịch chính
const KY_HIEU = { 'Work': 'W', 'Study': 'S', 'Ngày lễ ở Việt Nam': 'L' };

function doGet(e) {
  if (!e || !e.parameter || e.parameter.token !== TOKEN) return json_({ loi: 'sai token' });
  return json_({ luc: new Date().toISOString(), su_kien: suKien_(), viec: viec_() });
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

function viec_() {
  const ds = Tasks.Tasklists.list({ maxResults: 1 }).items || []; // danh sách mặc định = đầu tiên
  if (!ds.length) return [];
  const items = Tasks.Tasks.list(ds[0].id, { showCompleted: false, maxResults: 50 }).items || [];
  return items.filter(t => t.title).map(t => ({ tieu_de: t.title, han: t.due || null }));
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

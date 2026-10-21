#!/usr/bin/env node
// 🤖 아침칠판 MCP 서버 — 클로드가 "클로드 도우미" 계정으로 아침칠판(알림장·시간표·캘린더·급식)만 고친다.
// 권한은 Firebase 보안 규칙이 정한다(_members/<uid>.role = 'bot'): 점수·학생 정보·비밀번호는 읽지도 못함.
// 설정: %USERPROFILE%\.sinli-mcp\config.json  { "email": "...", "password": "...", "classId": "..." }
//   ※ 이 파일은 구글드라이브·GitHub에 두지 않는다(PC 로컬 전용).
// 바뀐 내용은 %USERPROFILE%\.sinli-mcp\changes.log 에 바뀌기 전/후로 기록(되돌리기용).
// 의존성 없음(Node 18+ 내장 fetch). 표준입출력 JSON-RPC(MCP).
'use strict';
const fs = require('fs'), path = require('path'), os = require('os');

const DIR = process.env.SINLI_MCP_DIR || path.join(os.homedir(), '.sinli-mcp');
const API_KEY = 'AIzaSyCrEfpzVS1YvORiM4HYRCryytj6Y-kG2fI'; // 웹앱에 공개된 Firebase 웹 키(비밀 아님)
const EMU = process.env.SINLI_EMU === '1';
const DB = EMU ? 'http://127.0.0.1:9400' : 'https://classscore-sinli-default-rtdb.firebaseio.com';
const DB_NS = EMU ? '&ns=classscore-sinli-default-rtdb' : '';
const AUTH = EMU ? 'http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1' : 'https://identitytoolkit.googleapis.com/v1';
const TOKEN = EMU ? 'http://127.0.0.1:9099/securetoken.googleapis.com/v1' : 'https://securetoken.googleapis.com/v1';

function loadConfig() {
  const f = path.join(DIR, 'config.json');
  if (!fs.existsSync(f)) throw new Error('설정 파일이 없어요: ' + f);
  const c = JSON.parse(fs.readFileSync(f, 'utf8'));
  ['email', 'password', 'classId'].forEach(k => { if (!c[k] || String(c[k]).includes('여기에')) throw new Error('config.json의 ' + k + ' 값을 채워 주세요'); });
  return c;
}

let tok = null; // { id, refresh, exp }
async function idToken() {
  if (tok && Date.now() < tok.exp) return tok.id;
  let r;
  if (tok && tok.refresh) {
    r = await fetch(TOKEN + '/token?key=' + API_KEY, { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: 'grant_type=refresh_token&refresh_token=' + encodeURIComponent(tok.refresh) }).then(x => x.json());
    if (r.id_token) { tok = { id: r.id_token, refresh: r.refresh_token, exp: Date.now() + (Number(r.expires_in) - 120) * 1000 }; return tok.id; }
  }
  const c = loadConfig();
  r = await fetch(AUTH + '/accounts:signInWithPassword?key=' + API_KEY, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: c.email, password: c.password, returnSecureToken: true }) }).then(x => x.json());
  if (!r.idToken) throw new Error('도우미 로그인 실패: ' + ((r.error && r.error.message) || '알 수 없음'));
  tok = { id: r.idToken, refresh: r.refreshToken, exp: Date.now() + (Number(r.expiresIn) - 120) * 1000 };
  return tok.id;
}

const SAFE_KEY = /^[^\/.#$\[\]\s]+$/; // Firebase 키에 못 쓰는 문자·경로 이동 차단 (한글 반 이름은 허용)
function roomPath(sub) {
  const cid = loadConfig().classId;
  if (!SAFE_KEY.test(cid)) throw new Error('classId 모양이 이상해요');
  sub.split('/').forEach(p => { if (!SAFE_KEY.test(p)) throw new Error('잘못된 경로: ' + sub); });
  return ['rooms', cid].concat(sub.split('/')).map(encodeURIComponent).join('/');
}
async function rest(method, sub, body) {
  const url = DB + '/' + roomPath(sub) + '.json?auth=' + (await idToken()) + DB_NS;
  const r = await fetch(url, { method, headers: { 'content-type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text();
  if (!r.ok) throw new Error(r.status === 401 ? '권한 없음(도우미가 이 반에 연결됐는지, 허용된 칸인지 확인)' : ('DB 오류 ' + r.status + ': ' + t.slice(0, 200)));
  return t ? JSON.parse(t) : null;
}
function logChange(what, before, after) {
  try { fs.mkdirSync(DIR, { recursive: true }); fs.appendFileSync(path.join(DIR, 'changes.log'), JSON.stringify({ at: new Date().toISOString(), what, before, after }) + '\n'); } catch (e) {}
}

const pad = n => String(n).padStart(2, '0');
function today() { const d = new Date(); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
function checkDate(s) { if (!/^\d{4}-\d{2}-\d{2}$/.test(s || '')) throw new Error('날짜는 YYYY-MM-DD 형식이어야 해요: ' + s); return s; }
const WD = ['일', '월', '화', '수', '목', '금', '토'];
function koDate(s) { const [y, m, d] = s.split('-').map(Number); const dt = new Date(y, m - 1, d); return m + '월 ' + d + '일 ' + WD[dt.getDay()] + '요일'; }

const BOARD_FIELDS = { morning: '아침 활동', notices: '전달 사항', allim: '알림장', safety: '안전 교육', birthday: '생일', dutyNums: '당번 번호', dutyTasks: '당번 할 일', date: '날짜 표시' };
const TT = { sub: 'ttSub', obj: 'ttObj', prep: 'ttPrep', page: 'ttPage', note: 'ttNote' };
function readable(d) {
  d = d || {}; const out = {};
  Object.keys(BOARD_FIELDS).forEach(k => { if (d[k]) out[BOARD_FIELDS[k] + ' (' + k + ')'] = d[k]; });
  const tt = [];
  for (let i = 1; i <= 6; i++) { const row = { 교시: i }; let any = false; Object.keys(TT).forEach(k => { const v = d[TT[k] + i]; if (v) { row[k] = v; any = true; } }); if (any) tt.push(row); }
  if (tt.length) out['시간표'] = tt;
  return out;
}

const tools = {
  board_get: {
    description: '아침칠판 내용을 읽는다(알림장·전달 사항·시간표 등). date를 주면 그날 기록, 없으면 지금 칠판.',
    inputSchema: { type: 'object', properties: { date: { type: 'string', description: 'YYYY-MM-DD (생략 시 오늘 칠판)' } } },
    async run({ date }) {
      if (date && checkDate(date) !== today()) return readable(await rest('GET', 'boardHistory/' + date));
      return readable(await rest('GET', 'skyDashboard'));
    }
  },
  board_update: {
    description: '아침칠판 칸을 고친다. 준 칸만 바뀌고 나머지는 그대로. 오늘이면 지금 칠판과 오늘 기록을 함께, 다른 날이면 그날 기록만 고친다. 시간표는 tt 배열(교시 1~6).',
    inputSchema: { type: 'object', properties: {
      date: { type: 'string', description: 'YYYY-MM-DD (생략 시 오늘)' },
      morning: { type: 'string' }, notices: { type: 'string' }, allim: { type: 'string' }, safety: { type: 'string' },
      birthday: { type: 'string' }, dutyNums: { type: 'string' }, dutyTasks: { type: 'string' },
      tt: { type: 'array', items: { type: 'object', properties: { period: { type: 'integer', minimum: 1, maximum: 6 }, sub: { type: 'string' }, obj: { type: 'string' }, prep: { type: 'string' }, page: { type: 'string' }, note: { type: 'string' } }, required: ['period'] } }
    } },
    async run(a) {
      const date = a.date ? checkDate(a.date) : today(), upd = {};
      Object.keys(BOARD_FIELDS).forEach(k => { if (k !== 'date' && typeof a[k] === 'string') upd[k] = a[k]; });
      (a.tt || []).forEach(r => { const p = Number(r.period); if (!(p >= 1 && p <= 6)) throw new Error('교시는 1~6'); Object.keys(TT).forEach(k => { if (typeof r[k] === 'string') upd[TT[k] + p] = r[k]; }); });
      if (!Object.keys(upd).length) throw new Error('바꿀 칸이 없어요');
      const isToday = date === today();
      const before = await rest('GET', isToday ? 'skyDashboard' : 'boardHistory/' + date) || {};
      if (!before.date) upd.date = koDate(date);
      if (isToday) await rest('PATCH', 'skyDashboard', upd);
      await rest('PATCH', 'boardHistory/' + date, upd);
      const prev = {}; Object.keys(upd).forEach(k => { prev[k] = before[k] === undefined ? null : before[k]; });
      logChange('board ' + date, prev, upd);
      return { 결과: '저장했어요', 날짜: date, 바뀐칸: Object.keys(upd), 바뀌기전: prev };
    }
  },
  calendar_list: {
    description: '캘린더 일정 목록(기간). type: event=행사, work=업무, birthday=생일.',
    inputSchema: { type: 'object', properties: { from: { type: 'string' }, to: { type: 'string' } }, required: ['from', 'to'] },
    async run({ from, to }) {
      checkDate(from); checkDate(to);
      const all = await rest('GET', 'calendarEvents') || {}, out = [];
      Object.keys(all).filter(d => d >= from && d <= to).sort().forEach(d => Object.keys(all[d] || {}).forEach(id => { const e = all[d][id] || {}; out.push({ date: d, id, type: e.type, text: e.text, detail: e.detail || '', done: !!e.done }); }));
      return out;
    }
  },
  calendar_add: {
    description: '캘린더에 일정을 추가한다.',
    inputSchema: { type: 'object', properties: { date: { type: 'string' }, text: { type: 'string' }, type: { type: 'string', enum: ['event', 'work', 'birthday'], default: 'event' }, detail: { type: 'string' } }, required: ['date', 'text'] },
    async run({ date, text, type, detail }) {
      checkDate(date);
      const r = await rest('POST', 'calendarEvents/' + date, { type: type || 'event', text: String(text), detail: String(detail || ''), done: false });
      logChange('calendar add ' + date, null, { id: r && r.name, text });
      return { 결과: '추가했어요', date, id: r && r.name };
    }
  },
  calendar_remove: {
    description: '캘린더 일정 하나를 지운다(calendar_list에서 받은 id).',
    inputSchema: { type: 'object', properties: { date: { type: 'string' }, id: { type: 'string' } }, required: ['date', 'id'] },
    async run({ date, id }) {
      checkDate(date);
      const before = await rest('GET', 'calendarEvents/' + date + '/' + id);
      if (!before) throw new Error('그 일정이 없어요');
      await rest('DELETE', 'calendarEvents/' + date + '/' + id);
      logChange('calendar remove ' + date + '/' + id, before, null);
      return { 결과: '지웠어요', 지운일정: before };
    }
  },
  meal_get: {
    description: '급식 메뉴 읽기(기간).',
    inputSchema: { type: 'object', properties: { from: { type: 'string' }, to: { type: 'string' } }, required: ['from', 'to'] },
    async run({ from, to }) {
      checkDate(from); checkDate(to);
      const all = await rest('GET', 'meals') || {}, out = {};
      Object.keys(all).filter(d => d >= from && d <= to).sort().forEach(d => { out[d] = all[d]; });
      return out;
    }
  },
  meal_set: {
    description: '급식 메뉴 쓰기. 메뉴는 줄바꿈으로 구분. 빈 문자열이면 그날 급식 지움.',
    inputSchema: { type: 'object', properties: { date: { type: 'string' }, menu: { type: 'string' } }, required: ['date', 'menu'] },
    async run({ date, menu }) {
      checkDate(date);
      const before = await rest('GET', 'meals/' + date);
      await rest('PUT', 'meals/' + date, menu ? String(menu) : null);
      logChange('meal ' + date, before, menu || null);
      return { 결과: menu ? '저장했어요' : '지웠어요', date };
    }
  },
  whoami: {
    description: '도우미가 연결된 반 이름 확인(연결 시험용).',
    inputSchema: { type: 'object', properties: {} },
    async run() { return { 반: await rest('GET', '_meta/name'), 오늘: today() }; }
  }
};

// ---- MCP(JSON-RPC over stdio) ----
function send(o) { process.stdout.write(JSON.stringify(o) + '\n'); }
async function handle(m) {
  if (m.method === 'initialize') return { protocolVersion: (m.params && m.params.protocolVersion) || '2025-06-18', capabilities: { tools: {} }, serverInfo: { name: 'sinli-board', version: '1.0.0' } };
  if (m.method === 'tools/list') return { tools: Object.keys(tools).map(n => ({ name: n, description: tools[n].description, inputSchema: tools[n].inputSchema })) };
  if (m.method === 'tools/call') {
    const t = tools[m.params.name]; if (!t) throw Object.assign(new Error('없는 도구'), { code: -32602 });
    try { const r = await t.run(m.params.arguments || {}); return { content: [{ type: 'text', text: JSON.stringify(r, null, 2) }] }; }
    catch (e) { return { content: [{ type: 'text', text: '오류: ' + e.message }], isError: true }; }
  }
  if (m.method === 'ping') return {};
  throw Object.assign(new Error('지원하지 않는 요청: ' + m.method), { code: -32601 });
}
let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buf += chunk; let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
    if (!line) continue;
    let m; try { m = JSON.parse(line); } catch (e) { continue; }
    if (m.id === undefined) continue; // 알림
    handle(m).then(result => send({ jsonrpc: '2.0', id: m.id, result }), e => send({ jsonrpc: '2.0', id: m.id, error: { code: e.code || -32603, message: e.message } }));
  }
});

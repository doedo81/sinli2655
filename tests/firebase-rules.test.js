// firebase-rules.json의 _members/$uid 쓰기 규칙을 JS로 옮겨 시나리오별로 검증한다.
// 실행: node tests/firebase-rules.test.js
//
// ⚠️ 한계: 이 테스트는 규칙 '식'을 그대로 옮긴 것이지 Firebase 엔진을 돌리는 게 아니다.
//    규칙 문법 자체의 오류는 잡지 못한다. 실제 게시 전 콘솔의 규칙 시뮬레이터로 한 번 더 확인할 것.
const fs = require('fs');
const path = require('path');

const RULES = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'firebase-rules.json'), 'utf8'));
const EXPR = RULES.rules.rooms.$cid._members.$uid['.write'];

let pass = 0, fail = 0;
function ok(label, actual, expected) {
  if (actual === expected) { pass++; console.log('  ok   ' + label); }
  else { fail++; console.log('  FAIL ' + label + '  (기대 ' + expected + ', 실제 ' + actual + ')'); }
}

// 규칙 식을 그대로 옮긴 판정기
function memberWriteAllowed(o) {
  const auth = o.authUid, $uid = o.targetUid;
  const meta = (o.room && o.room._meta) || null;
  const ownerUidExists = !!(meta && meta.ownerUid != null);
  const codeExists = !!(meta && meta.code != null);
  const newExists = o.newData != null;

  if (!(auth != null)) return false;
  if (!(auth === $uid)) return false;
  if (!newExists) return true;                                   // 자기 멤버십 삭제(탈퇴)
  if (!ownerUidExists) return true;                              // 주인 없는 방 → 자가 복구
  if (meta.ownerUid === auth) return true;                       // 내가 주인
  if (codeExists && o.newData.code === meta.code) return true;   // 코드를 아는 사람
  return false;
}

const ME = 'uid-me', OTHER = 'uid-other';
const CLAIMED = { _meta: { ownerUid: OTHER, code: 'AB23CD' } };
const MINE    = { _meta: { ownerUid: ME,    code: 'ZZ99YY' } };
const LEGACY  = {};                                    // 옛 방식 방: _meta 자체가 없음
const NOCODE  = { _meta: { ownerUid: OTHER } };        // 주인은 있는데 코드가 없는 방

console.log('앱의 정상 경로가 계속 동작하는가');
ok('classAddNew — 새 방 생성 (방이 아직 없음)',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: null, newData: { role: 'owner', name: '나' } }), true);
ok('switchAddClass — 새 방 추가 (동일 경로)',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: null, newData: { role: 'owner', name: '나' } }), true);
ok('ensureRoomWritable — 옛 방식 방 자가 복구',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: LEGACY, newData: { role: 'owner', name: '나' } }), true);
ok('ensureRoomWritable — 내가 주인인 방 재등록',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: MINE, newData: { role: 'owner', name: '나' } }), true);
ok('joinClassByCode — 올바른 코드로 전담 참여',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: CLAIMED, newData: { role: 'subject', name: '나', code: 'AB23CD' } }), true);
ok('본인 멤버십 삭제(탈퇴)',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: CLAIMED, newData: null }), true);

console.log('공격 시나리오가 막히는가');
ok('남의 방에 코드 없이 자가 등록',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: CLAIMED, newData: { role: 'owner', name: '침입자' } }), false);
ok('남의 방에 틀린 코드로 자가 등록',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: CLAIMED, newData: { role: 'subject', name: '침입자', code: 'WRONG1' } }), false);
ok('코드 없는 방에 code 필드를 비우고 등록 (null === null 우회 시도)',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: NOCODE, newData: { role: 'owner', name: '침입자' } }), false);
ok('코드 없는 방에 아무 코드나 넣고 등록',
   memberWriteAllowed({ authUid: ME, targetUid: ME, room: NOCODE, newData: { role: 'owner', name: '침입자', code: 'GUESS1' } }), false);
ok('남의 uid 자리에 멤버십 심기',
   memberWriteAllowed({ authUid: ME, targetUid: OTHER, room: LEGACY, newData: { role: 'owner', name: '침입자' } }), false);
ok('비로그인 상태 쓰기',
   memberWriteAllowed({ authUid: null, targetUid: ME, room: LEGACY, newData: { role: 'owner', name: '익명' } }), false);
ok('남의 멤버십 삭제',
   memberWriteAllowed({ authUid: ME, targetUid: OTHER, room: CLAIMED, newData: null }), false);

console.log('규칙 파일 자체 점검');
ok('_members 규칙 식이 존재한다', typeof EXPR === 'string' && EXPR.length > 0, true);
ok('식이 auth.uid === $uid 를 요구한다', EXPR.indexOf('auth.uid === $uid') > -1, true);
ok('식이 _meta.code 존재를 확인한다', EXPR.indexOf("child('code').exists()") > -1, true);
// 무인증 공개 읽기(".read": true)가 늘어나지 않았는지 — 늘면 개인정보 노출 위험
ok('무인증 공개 읽기는 정확히 3곳 (studentCodes, dashboardDefaults, rpg)',
   JSON.stringify(RULES).split('".read":true').length - 1, 3);
ok('rooms 최상위 읽기는 로그인 필요',
   RULES.rules.rooms.$cid['.read'].indexOf('auth != null') === 0, true);
ok('skyDashboard·boardHistory에 공개 읽기가 없다',
   RULES.rules.rooms.$cid.skyDashboard === undefined && RULES.rules.rooms.$cid.boardHistory === undefined, true);

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);

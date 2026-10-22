// 주제일기 보안 규칙을 실제 Firebase RTDB 에뮬레이터로 검증 (규칙 식 흉내가 아니라 진짜 엔진)
// 준비: npm i firebase-tools@13 @firebase/rules-unit-testing@3 firebase@10   (자바 필요)
// 실행: npx firebase emulators:exec --only database --project diary-test "node tests/diary-rules.emulator.test.js firebase-rules.json"
const fs = require('fs');
const { initializeTestEnvironment, assertSucceeds, assertFails } = require('@firebase/rules-unit-testing');
const { ref, get, set, update, remove } = require('firebase/database');

const RULES = fs.readFileSync(process.argv[2], 'utf8');
const R = 'rooms/ROOM1';
let pass = 0, fail = 0;
async function t(label, p) {
  try { await p; pass++; console.log('  ok   ' + label); }
  catch (e) { fail++; console.log('  FAIL ' + label + ' — ' + (e && e.message)); }
}

(async () => {
  const env = await initializeTestEnvironment({
    projectId: 'diary-test',
    database: { host: '127.0.0.1', port: 9000, rules: RULES }
  });
  await env.withSecurityRulesDisabled(async (ctx) => {
    await set(ref(ctx.database(), R), {
      _meta: { ownerUid: 'teacher', code: 'AB12CD' },
      _members: { teacher: { role: 'owner' } },
      secrets: { pw: { '3': 'h3', '5': 'h5' } },
      studentSessions: { stu3: { num: '3', h: 'h3' }, stu5: { num: '5', h: 'h5' } },
      diary: {
        topics: { T1: { title: '요술램프', date: '2026-10-22', minChars: 10, guide: 'g', maxRev: 1 }, T0: { title: '못 고치는 주제', date: '2026-10-21', maxRev: 0 } },
        entries: { '5': { T1: { text: '5번 친구의 비밀 일기', createdAt: 1, updatedAt: 1 } } },
        feedback: { '3': { T1: { stamp: 'good', comment: '잘했어' } }, '5': { T1: { stamp: 'best' } } }
      }
    });
  });
  const anon = { firebase: { sign_in_provider: 'anonymous' } };
  const s3 = env.authenticatedContext('stu3', anon).database();
  const nos = env.authenticatedContext('stranger', anon).database();
  const tch = env.authenticatedContext('teacher', { firebase: { sign_in_provider: 'google.com' } }).database();
  const unauth = env.unauthenticatedContext().database();

  console.log('학생(3번) — 되어야 하는 것');
  await t('주제 읽기', assertSucceeds(get(ref(s3, R + '/diary/topics'))));
  await t('처음 내기 (rev 0)', assertSucceeds(set(ref(s3, R + '/diary/entries/3/T1'), { text: '나의 소원은 세 가지다', rev: 0, createdAt: 2, updatedAt: 2 })));
  await t('내 일기 읽기', assertSucceeds(get(ref(s3, R + '/diary/entries/3'))));
  await t('고쳐 내기 1번 (rev 1, 이 주제는 1번까지)', assertSucceeds(set(ref(s3, R + '/diary/entries/3/T1'), { text: '고친 글', rev: 1, createdAt: 2, updatedAt: 3 })));
  await t('선생님 한마디(내 것) 읽기', assertSucceeds(get(ref(s3, R + '/diary/feedback/3'))));
  await t('못 고치는 주제에 처음 내기', assertSucceeds(set(ref(s3, R + '/diary/entries/3/T0'), { text: '한 번에', rev: 0, createdAt: 1, updatedAt: 1 })));

  console.log('학생(3번) — 막혀야 하는 것');
  await t('친구(5번) 일기 읽기', assertFails(get(ref(s3, R + '/diary/entries/5'))));
  await t('친구(5번) 일기 한 편 읽기', assertFails(get(ref(s3, R + '/diary/entries/5/T1'))));
  await t('일기 전체 한꺼번에 읽기', assertFails(get(ref(s3, R + '/diary'))));
  await t('entries 전체 읽기', assertFails(get(ref(s3, R + '/diary/entries'))));
  await t('친구 한마디 읽기', assertFails(get(ref(s3, R + '/diary/feedback/5'))));
  await t('친구(5번) 칸에 쓰기', assertFails(set(ref(s3, R + '/diary/entries/5/T1'), { text: '장난' })));
  await t('도장·한마디 스스로 쓰기', assertFails(set(ref(s3, R + '/diary/feedback/3/T1'), { stamp: 'best', best: true })));
  await t('상점 받음 표시 스스로 하기', assertFails(set(ref(s3, R + '/diary/feedback/3/T1/rewarded'), true)));
  await t('주제 만들기', assertFails(set(ref(s3, R + '/diary/topics/T9'), { title: 'x', date: '2026-10-22' })));
  await t('없는 주제에 쓰기', assertFails(set(ref(s3, R + '/diary/entries/3/NOPE'), { text: 'x', rev: 0 })));
  await t('고쳐 쓰기 기회를 넘겨서 내기 (rev 2 > 1)', assertFails(set(ref(s3, R + '/diary/entries/3/T1'), { text: '또 고침', rev: 2, createdAt: 2, updatedAt: 4 })));
  await t('못 고치는 주제 고치기 (rev 1 > 0)', assertFails(set(ref(s3, R + '/diary/entries/3/T0'), { text: '고침', rev: 1, createdAt: 1, updatedAt: 2 })));
  await t('rev를 그대로 두고 덮어쓰기', assertFails(set(ref(s3, R + '/diary/entries/3/T0'), { text: '몰래 고침', rev: 0, createdAt: 1, updatedAt: 2 })));
  await t('내 일기 지우기 (지우고 다시 내서 횟수 초기화 방지)', assertFails(remove(ref(s3, R + '/diary/entries/3/T1'))));
  await t('rev 없이 쓰기', assertFails(set(ref(s3, R + '/diary/entries/3/T9X'), { text: 'x' })));
  await t('5001자 쓰기', assertFails(set(ref(s3, R + '/diary/entries/3/T0'), { text: 'a'.repeat(5001), rev: 1 })));
  await t('text 없이 쓰기', assertFails(set(ref(s3, R + '/diary/entries/3/T0'), { body: 'x', rev: 1 })));
  await t('text를 숫자로 쓰기', assertFails(set(ref(s3, R + '/diary/entries/3/T0'), { text: 123, rev: 1 })));

  console.log('로그인 안 한 학생·외부인');
  await t('세션 없는 익명 — 주제 읽기', assertFails(get(ref(nos, R + '/diary/topics'))));
  await t('세션 없는 익명 — 3번 칸 쓰기', assertFails(set(ref(nos, R + '/diary/entries/3/T1'), { text: 'x' })));
  await t('비로그인 — 주제 읽기', assertFails(get(ref(unauth, R + '/diary/topics'))));

  console.log('선생님');
  await t('주제 내기', assertSucceeds(set(ref(tch, R + '/diary/topics/T2'), { title: '좋은 친구란', date: '2026-10-23', minChars: 100, guide: '' })));
  await t('반 전체 일기 읽기', assertSucceeds(get(ref(tch, R + '/diary/entries'))));
  await t('도장·한마디 쓰기', assertSucceeds(update(ref(tch, R + '/diary/feedback/5/T1'), { stamp: 'great', comment: '멋져', best: true, at: 5 })));
  await t('AI 채점 결과 저장(선생님 기기)', assertSucceeds(update(ref(tch, R + '/diary/feedback/5/T1'), { ai: { score: 82, items: [{ name: '내용', got: 25, max: 30 }], forUpdatedAt: 1 }, aiClaim: null })));
  await t('학생이 AI 점수 조작', assertFails(set(ref(s3, R + '/diary/feedback/3/T1/ai/score'), 100)));
  await t('상점 지급(성장+받음 표시 한꺼번에)', assertSucceeds(update(ref(tch, R), { 'rpg/students/5': { xp: 20, stats: { wis: 1 } }, 'diary/feedback/5/T1/rewarded': true })));
  await t('주제+일기 함께 지우기', assertSucceeds(update(ref(tch, R + '/diary'), { 'topics/T1': null, 'entries/5/T1': null, 'feedback/5/T1': null })));

  console.log('\n' + pass + ' passed, ' + fail + ' failed');
  await env.cleanup();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });

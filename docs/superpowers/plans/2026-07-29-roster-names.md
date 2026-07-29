# 자리배치·과제관리 학생 이름 표시 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 학생 이름을 로그인해야 읽히는 별도 노드에 저장하고, 자리배치·과제관리·제출통계에서 번호와 함께 보여준다.

**Architecture:** 이름 포함 명단은 `rooms/$cid/settings/rosterNames`(상위 `rooms/$cid` 규칙 상속 → 로그인 필요)에, 기존 공개 노드 `settings/dashboardDefaults/roster`에는 이름을 뺀 "번호 성별"만 저장한다. 읽을 때 `rosterNames`가 있으면 그것을 기존 전역 `globalStudentRosterStr`에 넣으므로 자리배치·성장 탭은 코드를 고치지 않아도 이름이 나온다. 과제관리·제출통계만 렌더링을 수정한다.

**Tech Stack:** 단일 파일 `index.html` (바닐라 JS + Firebase RTDB 8.10.1). 빌드 도구 없음. 테스트는 의존성 없는 Node 스크립트로 `index.html`에서 순수 함수를 잘라내 검증한다.

## Global Constraints

- 보안 규칙(`firebase-rules.json`)은 **수정하지 않는다.** `rosterNames`는 규칙 변경 없이 보호된다.
- 학생 핸드폰 로그인 경로 `rpgStudentInit()`은 **수정하지 않는다.** 계속 공개 `roster`만 읽는다.
- 자리배치(`nsParseRoster`)와 성장 탭(`rpgParseRosterStr`)의 파싱 로직은 **수정하지 않는다.**
- 이름이 없는 학생은 기존과 동일하게 번호만 표시한다.
- 사용자 입력 이름은 화면에 넣기 전 반드시 `escapeHtml()`을 거친다.
- 성별 판정은 공백 토큰 단위(`tok === '남'`)로만 한다. `includes('남')`은 `김남수`를 오판정하므로 금지.
- 명단 입력 형식은 기존 그대로 `1 김민수 남` (placeholder 1172행에 이미 안내됨).
- **Task 5 전까지 `git push` 금지.** main에 푸시하면 선생님이 매일 쓰는 라이브 사이트로 즉시 배포된다. 각 Task는 로컬 커밋까지만 한다.

## File Structure

| 파일 | 역할 | 변경 |
|---|---|---|
| `index.html` | 앱 전체 (단일 파일, 레포 관행) | 수정 |
| `tests/roster-names.test.js` | 순수 함수 단위 테스트 (Node, 무의존성) | 신규 |

`index.html`은 이미 4,900줄이 넘지만 이 레포는 단일 파일 배포가 전제(GitHub Pages, 빌드 없음)이므로 분할하지 않는다. 새 함수는 관련 함수 근처(`rpgParseRoster` 아래)에 모아 둔다.

---

### Task 1: 순수 함수 2개 + 테스트 하네스

이름 분리와 번호→이름 매핑을 담당하는 순수 함수를 만든다. DB·DOM에 의존하지 않으므로 단위 테스트가 가능하다.

**Files:**
- Test: `tests/roster-names.test.js` (신규)
- Modify: `index.html` — `rpgParseRoster()` 정의(4590행) 바로 아래에 추가

**Interfaces:**
- Consumes: `rpgParseRosterStr(str)` → `[{id:number, name:string, gender:'M'|'F'|'U'}]` (4569행, 기존 함수. 이름이 없으면 `name`이 `"3번"` 형태가 된다)
- Produces:
  - `rosterStripNames(txt: string) → string` — 이름을 뺀 "번호 성별" 여러 줄
  - `rosterNameMapFrom(str: string) → {[num]: string}` — 이름이 있는 학생만 담긴 맵
  - `rosterNameMap() → {[num]: string}` — 위를 `globalStudentRosterStr`로 호출

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/roster-names.test.js` 생성:

```js
// 의존성 없는 테스트. 실행: node tests/roster-names.test.js
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

// index.html 인라인 스크립트에서 함수 하나를 중괄호 짝으로 잘라낸다.
// 주의: 대상 함수 안에 짝이 안 맞는 중괄호가 문자열/정규식으로 들어있으면 안 된다.
function extractFn(name) {
  const start = SRC.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('함수를 찾을 수 없음: ' + name);
  let depth = 0, began = false;
  for (let j = SRC.indexOf('{', start); j < SRC.length; j++) {
    if (SRC[j] === '{') { depth++; began = true; }
    else if (SRC[j] === '}') { depth--; if (began && depth === 0) return SRC.slice(start, j + 1); }
  }
  throw new Error('닫는 중괄호를 못 찾음: ' + name);
}

eval([
  extractFn('rpgParseRosterStr'),
  extractFn('rosterStripNames'),
  extractFn('rosterNameMapFrom'),
].join('\n'));

let pass = 0, fail = 0;
function eq(label, actual, expected) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a === e) { pass++; console.log('  ok   ' + label); }
  else { fail++; console.log('  FAIL ' + label + '\n       기대: ' + e + '\n       실제: ' + a); }
}

console.log('rosterStripNames — 공개 노드용으로 이름을 걷어낸다');
eq('이름+성별 → 번호+성별', rosterStripNames('1 김민수 남\n2 이서연 여'), '1 남\n2 여');
eq('기존 탭 구분 데이터 유지', rosterStripNames('1\t여\n2\t남'), '1 여\n2 남');
eq('이름에 남/여가 있어도 오작동 없음', rosterStripNames('3 김남수 남\n4 남궁여진 여'), '3 남\n4 여');
eq('성별이 없으면 번호만', rosterStripNames('7 박하늘'), '7');
eq('빈 줄은 버린다', rosterStripNames('1 김민수 남\n\n  \n2 이서연 여'), '1 남\n2 여');
eq('번호 없는 줄은 버린다', rosterStripNames('머리말\n1 김민수 남'), '1 남');
eq('빈 입력', rosterStripNames(''), '');
eq('null 입력', rosterStripNames(null), '');

console.log('rosterNameMapFrom — 번호 → 이름 (이름 없으면 키 없음)');
eq('이름 있는 학생만', rosterNameMapFrom('1 김민수 남\n2 여'), { 1: '김민수' });
eq('전원 이름 있음', rosterNameMapFrom('1 김민수 남\n2 이서연 여'), { 1: '김민수', 2: '이서연' });
eq('전원 이름 없음', rosterNameMapFrom('1 남\n2 여'), {});
eq('빈 입력', rosterNameMapFrom(''), {});

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

실행: `node tests/roster-names.test.js`
기대: `Error: 함수를 찾을 수 없음: rosterStripNames` 로 종료

- [ ] **Step 3: 최소 구현 추가**

`index.html`에서 `function rpgParseRoster(){ return rpgParseRosterStr(globalStudentRosterStr); }` (4590행) **바로 다음 줄**에 삽입:

```js

        // 📛 명단에서 이름을 걷어내 "번호 성별"만 남긴다 (무인증 공개 노드 roster 전용).
        //    성별 판정은 반드시 공백 토큰 단위 — '김남수' 같은 이름을 성별로 오인하면 안 된다.
        function rosterStripNames(txt){
            return (txt || '').split('\n').map(function(line){
                var t = line.trim(); if(!t) return '';
                var idm = t.match(/\d+/); if(!idm) return '';
                var gender = '';
                t.split(/\s+/).forEach(function(tok){ if(tok === '남' || tok === '여') gender = tok; });
                return gender ? (idm[0] + ' ' + gender) : idm[0];
            }).filter(Boolean).join('\n');
        }

        // 번호 → 이름 맵. 이름이 없는 학생은 키를 만들지 않는다(호출부에서 번호만 쓰도록).
        function rosterNameMapFrom(str){
            var map = {};
            rpgParseRosterStr(str).forEach(function(s){
                if(s.name && s.name !== (s.id + '번')) map[s.id] = s.name;
            });
            return map;
        }
        function rosterNameMap(){ return rosterNameMapFrom(globalStudentRosterStr); }
```

- [ ] **Step 4: 테스트 통과 확인**

실행: `node tests/roster-names.test.js`
기대: `12 passed, 0 failed`, 종료 코드 0

- [ ] **Step 5: 커밋**

```bash
git add tests/roster-names.test.js index.html
git commit -m "명단 이름 분리·조회 순수 함수 추가 (rosterStripNames, rosterNameMap)"
```

---

### Task 2: 저장·읽기 배선

이름을 비공개 노드에 쓰고, 로그인 상태에서 그것을 읽어 `globalStudentRosterStr`에 넣는다.

저장(쓰기)만 먼저 하고 읽기를 나중에 하면 이름이 화면에서 사라지는 중간 상태가 생기므로 **한 Task로 묶는다.**

**Files:**
- Modify: `index.html` — 5곳 (아래 각 Step 참조)

**Interfaces:**
- Consumes: `rosterStripNames(txt)` (Task 1)
- Produces: `rosterNamesRef() → firebase.database.Reference` — 현재 방의 `settings/rosterNames` 참조

- [ ] **Step 1: rosterNamesRef 헬퍼 추가**

Task 1에서 추가한 `rosterNameMap()` 정의 **바로 다음 줄**에 삽입:

```js

        // 이름 포함 명단은 dashboardDefaults 바깥에 둔다.
        // → 상위 rooms/$cid 규칙(로그인 필요)을 상속받아 학생 폰·외부에서는 읽히지 않는다.
        function rosterNamesRef(){ return db.ref('rooms/' + currentRoom + '/settings/rosterNames'); }
```

- [ ] **Step 2: enterRoom 읽기 경로 수정 (1803~1807행)**

찾을 코드:

```js
            settingsRef.once('value').then(snap => {
                if(snap.exists()){
                    const s = snap.val();
                    globalTotalStudents = s.totalStudents || 24;
                    globalStudentRosterStr = s.roster || "";
```

바꿀 코드:

```js
            Promise.all([
                settingsRef.once('value'),
                // 이름은 로그인해야 읽힌다. 못 읽으면(권한 없음·아직 없음) 공개 명단으로 폴백.
                rosterNamesRef().once('value').catch(function(){ return null; })
            ]).then(([snap, nameSnap]) => {
                if(snap.exists()){
                    const s = snap.val();
                    const savedNames = nameSnap && nameSnap.val();
                    globalTotalStudents = s.totalStudents || 24;
                    globalStudentRosterStr = savedNames || s.roster || "";
```

나머지 줄(`globalSeparatedStr` 이하와 `}).catch(e => console.error("설정 로드 오류:", e));`)은 그대로 둔다.

- [ ] **Step 3: openSettingsModal 읽기 경로 수정 (4228, 4237행)**

찾을 코드:

```js
            settingsRef.once('value').then(snap => {
                const d = snap.val() || {
```

바꿀 코드:

```js
            Promise.all([
                settingsRef.once('value'),
                rosterNamesRef().once('value').catch(function(){ return null; })
            ]).then(([snap, nameSnap]) => {
                const d = snap.val() || {
```

이어서 찾을 코드:

```js
                document.getElementById('set-student-roster').value = d.roster || "";
```

바꿀 코드:

```js
                const savedNames = nameSnap && nameSnap.val();
                document.getElementById('set-student-roster').value = savedNames || d.roster || "";
```

- [ ] **Step 4: saveSettingsData 저장 경로 수정 (4266~4268, 4278, 4292행)**

찾을 코드:

```js
        function saveSettingsData() {
            const data = {
                totalStudents: parseInt(document.getElementById('set-total-students').value) || 24,
```

바꿀 코드:

```js
        function saveSettingsData() {
            const rosterRaw = document.getElementById('set-student-roster').value || "";
            const data = {
                totalStudents: parseInt(document.getElementById('set-total-students').value) || 24,
```

이어서 찾을 코드:

```js
                roster: document.getElementById('set-student-roster').value || "",
```

바꿀 코드 (공개 노드에는 이름을 넣지 않는다):

```js
                roster: rosterStripNames(rosterRaw),
```

이어서 찾을 코드:

```js
            globalStudentRosterStr = data.roster;
```

바꿀 코드 (저장 직후 화면에서 이름이 사라지면 안 된다):

```js
            globalStudentRosterStr = rosterRaw;
```

이어서 찾을 코드:

```js
            settingsRef.set(data).then(() => {
                alert("설정이 성공적으로 저장되었습니다!"); 
                closeSettingsModal();
            }).catch(e => {
```

바꿀 코드:

```js
            Promise.all([
                settingsRef.set(data),
                rosterNamesRef().set(rosterRaw)
            ]).then(() => {
                alert("설정이 성공적으로 저장되었습니다!"); 
                closeSettingsModal();
            }).catch(e => {
```

- [ ] **Step 5: rpgWriteRoster 저장 경로 수정 (4604~4606행)**

찾을 코드:

```js
        function rpgWriteRoster(txt, doneMsg){
            globalStudentRosterStr = txt; // 로컬 상태 즉시 반영 (연속 조작 안전)
            return settingsRef.update({ roster: txt }).then(() => {
```

바꿀 코드:

```js
        function rpgWriteRoster(txt, doneMsg){
            globalStudentRosterStr = txt; // 로컬 상태 즉시 반영 (연속 조작 안전)
            // 이름 포함 원본은 비공개 노드에, 공개 노드에는 이름을 뺀 판만 저장
            return Promise.all([
                settingsRef.update({ roster: rosterStripNames(txt) }),
                rosterNamesRef().set(txt)
            ]).then(() => {
```

- [ ] **Step 6: 문법 검사**

실행:

```bash
node -e "const fs=require('fs'),vm=require('vm');const s=fs.readFileSync('index.html','utf8');const m=s.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/);new vm.Script(m[1]);console.log('문법 OK');"
```

기대: `문법 OK`

- [ ] **Step 7: 기존 테스트가 계속 통과하는지 확인**

실행: `node tests/roster-names.test.js`
기대: `12 passed, 0 failed`

- [ ] **Step 8: 커밋**

```bash
git add index.html
git commit -m "이름 포함 명단을 비공개 노드 rosterNames에 분리 저장"
```

---

### Task 3: 과제 관리 제출 버튼에 이름 표시

번호 위, 이름 아래 2단. 셀 폭(55px)과 한 줄 개수는 그대로 둔다.

**Files:**
- Modify: `index.html` — CSS(187행 아래), `hwStudentBtnHtml` 신규, `renderHomeworkList`(4148, 4156행)
- Test: `tests/roster-names.test.js` (테스트 추가)

**Interfaces:**
- Consumes: `rosterNameMap()` (Task 1), `escapeHtml(s)` (2571행, 기존)
- Produces: `hwStudentBtnHtml(hwId: string, num: number, btnClass: string, name?: string) → string`

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/roster-names.test.js`의 `extractFn` 목록에 `escapeHtml`과 `hwStudentBtnHtml`을 추가한다. 즉

```js
eval([
  extractFn('rpgParseRosterStr'),
  extractFn('rosterStripNames'),
  extractFn('rosterNameMapFrom'),
].join('\n'));
```

를 다음으로 바꾼다:

```js
eval([
  extractFn('escapeHtml'),
  extractFn('rpgParseRosterStr'),
  extractFn('rosterStripNames'),
  extractFn('rosterNameMapFrom'),
  extractFn('hwStudentBtnHtml'),
].join('\n'));
```

그리고 `console.log('\n' + pass + ...)` 줄 **바로 앞**에 다음을 추가한다:

```js
console.log('hwStudentBtnHtml — 과제 제출 체크 버튼');
eq('이름 있으면 번호 위·이름 아래',
   hwStudentBtnHtml('h1', 3, 'done', '박준호'),
   '<button class="student-btn done" onclick="cycleH(\'h1\',3)"><span class="sb-num">3</span><span class="sb-name">박준호</span></button>');
eq('이름 없으면 번호만 (지금과 동일)',
   hwStudentBtnHtml('h1', 3, '', undefined),
   '<button class="student-btn " onclick="cycleH(\'h1\',3)">3</button>');
eq('면제 상태 클래스 유지',
   hwStudentBtnHtml('h1', 5, 'excused', '김민수').indexOf('student-btn excused') > -1, true);
eq('이름 XSS 차단',
   hwStudentBtnHtml('h1', 3, '', '<img src=x onerror=alert(1)>').indexOf('<img') > -1, false);
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

실행: `node tests/roster-names.test.js`
기대: `Error: 함수를 찾을 수 없음: hwStudentBtnHtml` 로 종료

- [ ] **Step 3: CSS 추가 (187행 `.student-btn.excused` 다음 줄)**

찾을 코드:

```css
        .student-btn.excused { background-color: white; border: 1px dashed #ccc; color: #b0bec5; text-decoration: line-through; box-shadow: none;}
```

바로 다음 줄에 삽입:

```css
        .student-btn .sb-num { display:block; line-height:1.1; }
        .student-btn .sb-name { display:block; font-size:12px; font-weight:700; line-height:1.2; margin-top:2px; opacity:0.85; }
```

- [ ] **Step 4: hwStudentBtnHtml 구현**

`renderHomeworkList` 정의(4147행) **바로 앞**에 삽입:

```js
        // 과제 제출 체크 버튼 하나. 이름이 없으면 번호만 (기존과 같은 모양).
        // 템플릿 리터럴 대신 문자열 연결을 쓰는 이유: 테스트 하네스가 중괄호 짝으로 함수를 잘라낸다.
        function hwStudentBtnHtml(hwId, num, btnClass, name){
            var label = name
                ? '<span class="sb-num">' + num + '</span><span class="sb-name">' + escapeHtml(name) + '</span>'
                : String(num);
            return '<button class="student-btn ' + btnClass + '" onclick="cycleH(\'' + escapeHtml(hwId) + '\',' + num + ')">' + label + '</button>';
        }

```

- [ ] **Step 5: renderHomeworkList에서 사용 (4148, 4156행)**

찾을 코드:

```js
            const div = document.getElementById('homework-list'); div.innerHTML = ''; const showA = document.getElementById('show-archived').checked;
```

바꿀 코드 (맵을 과제마다가 아니라 한 번만 만든다):

```js
            const div = document.getElementById('homework-list'); div.innerHTML = ''; const showA = document.getElementById('show-archived').checked;
            const nameMap = rosterNameMap();
```

이어서 찾을 코드:

```js
                    btns += `<button class="student-btn ${btnClass}" onclick="cycleH('${hw.id}',${i})">${i}</button>`;
```

바꿀 코드:

```js
                    btns += hwStudentBtnHtml(hw.id, i, btnClass, nameMap[i]);
```

- [ ] **Step 6: 테스트 통과 확인**

실행: `node tests/roster-names.test.js`
기대: `16 passed, 0 failed`

- [ ] **Step 7: 커밋**

```bash
git add index.html tests/roster-names.test.js
git commit -m "과제 관리 제출 버튼에 번호+이름 2단 표시"
```

---

### Task 4: 제출 통계에 이름 표시

같은 과제관리 탭의 "제출 통계" 뷰가 `1번 학생`으로만 나온다. `1번 김민수`로 바꾼다.

**Files:**
- Modify: `index.html` — `renderStats` 학생별 구간 (4209, 4220행)

**Interfaces:**
- Consumes: `rosterNameMap()` (Task 1), `escapeHtml(s)` (2571행, 기존)
- Produces: 없음

- [ ] **Step 1: 이름 맵 준비 (4209행)**

찾을 코드:

```js
                let students = {}; let maxTotal = 24;
```

바꿀 코드:

```js
                let students = {}; let maxTotal = 24;
                const nameMap = rosterNameMap();
```

- [ ] **Step 2: 표시 문구 변경 (4220행)**

찾을 코드 (긴 한 줄 중 이 부분만):

```
margin-bottom:8px;">${i}번 학생</div>
```

바꿀 코드:

```
margin-bottom:8px;">${i}번 ${escapeHtml(nameMap[i] || '학생')}</div>
```

- [ ] **Step 3: 문법 검사**

실행:

```bash
node -e "const fs=require('fs'),vm=require('vm');const s=fs.readFileSync('index.html','utf8');const m=s.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/);new vm.Script(m[1]);console.log('문법 OK');"
```

기대: `문법 OK`

- [ ] **Step 4: 기존 테스트 통과 확인**

실행: `node tests/roster-names.test.js`
기대: `16 passed, 0 failed`

- [ ] **Step 5: 커밋**

```bash
git add index.html
git commit -m "제출 통계에 학생 이름 표시"
```

---

### Task 5: 통합 검증 후 배포

여기서 처음으로 푸시한다. 푸시 즉시 라이브 사이트에 배포되므로 그 전에 로컬에서 전부 확인한다.

**Files:** 없음 (검증·배포만)

**Interfaces:** 없음

- [ ] **Step 1: 로컬 서버로 앱 띄우기**

```bash
py -3 -m http.server 8790
```

브라우저에서 `http://127.0.0.1:8790/index.html` 열고 로그인.

- [ ] **Step 2: 이름 입력하고 저장**

설정(⚙️) → 학생 명단에 아래를 넣고 저장:

```
1 김민수 남
2 이서연 여
3 남
```

3번은 일부러 이름을 비운다.

- [ ] **Step 3: 화면 확인 (4가지)**

- 자리배치 탭 → `김민수`, `이서연`, `3번`이 나오는지 (**코드를 안 고쳤는데도 나와야 한다**)
- 과제 관리 → 제출 버튼이 번호 위·이름 아래 2단인지, 3번은 번호만인지
- 과제 관리 → 제출 통계 → `1번 김민수`, `3번 학생`인지
- 제출 버튼을 눌러 미제출 → 제출 → 면제 3상태가 그대로 도는지

- [ ] **Step 4: DB 분리 저장 확인 (가장 중요)**

무인증 상태로 두 경로를 찌른다. `<반이름>`은 실제 방 이름으로 바꾼다.

```bash
BASE=https://classscore-sinli-default-rtdb.firebaseio.com
curl -s "$BASE/rooms/<반이름>/settings/dashboardDefaults/roster.json"
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/rooms/<반이름>/settings/rosterNames.json"
```

기대:
- 첫 번째: `"1 남\n2 여\n3 남"` — **이름이 없어야 한다**
- 두 번째: `401` — **무인증으로 읽히면 안 된다**

둘 중 하나라도 다르면 여기서 멈추고 원인을 찾는다. 절대 푸시하지 않는다.

- [ ] **Step 5: 학생 핸드폰 로그인 확인**

브라우저 시크릿 창에서 학생 로그인 화면으로 접속해 번호+비밀번호로 로그인되는지 확인한다.
(무인증으로 공개 `roster`를 읽어 번호를 검증하는 경로가 살아 있어야 한다)

- [ ] **Step 6: 푸시**

```bash
git push origin main
```

- [ ] **Step 7: 배포 반영 확인**

```bash
curl -s "https://doedo81.github.io/sinli2655/index.html?cb=1" | grep -c "rosterStripNames"
```

기대: `1` 이상. 0이면 GitHub Pages 빌드를 1~2분 더 기다렸다 재확인한다.

---

## Self-Review

**Spec coverage:**

| 스펙 항목 | 담당 Task |
|---|---|
| 이름을 `settings/rosterNames`에 분리 저장 | Task 2 |
| 공개 `roster`에는 번호+성별만 (토큰 단위 성별 판정) | Task 1, 2 |
| 저장 2곳 (`saveSettingsData`, `rpgWriteRoster`) | Task 2 Step 4, 5 |
| 읽기 2곳 (`enterRoom`, `openSettingsModal`) | Task 2 Step 2, 3 |
| 저장 직후 `globalStudentRosterStr`에 이름 포함 원본 | Task 2 Step 4, 5 |
| `rpgStudentInit` 미수정 | Global Constraints (명시적 금지) |
| 과제 관리 버튼 2단 (55px 유지) | Task 3 |
| 제출 통계에 이름 | Task 4 |
| 이름 없으면 번호만 | Task 1 (`rosterNameMapFrom`), Task 3 (`hwStudentBtnHtml`) |
| `escapeHtml` 적용 | Task 3, 4 |
| 마이그레이션 불필요 (폴백) | Task 2 Step 2, 3 (`savedNames || s.roster`) |
| 보안 규칙 미변경 | Global Constraints |
| 검증 6항목 | Task 5 |

빠진 항목 없음.

**Placeholder scan:** TBD/TODO/"적절히 처리" 없음. 모든 코드 단계에 실제 코드 블록이 있고, 찾을 코드/바꿀 코드를 전문으로 적었다.

**Type consistency:**
- `rosterStripNames(txt: string) → string` — Task 1 정의, Task 2 Step 4·5에서 사용. 일치.
- `rosterNameMapFrom(str) → {[num]: string}` / `rosterNameMap()` — Task 1 정의, Task 3 Step 5·Task 4 Step 1에서 사용. 일치.
- `rosterNamesRef() → Reference` — Task 2 Step 1 정의, 같은 Task Step 2~5에서 사용. 일치.
- `hwStudentBtnHtml(hwId, num, btnClass, name)` — Task 3 Step 4 정의, Step 5에서 인자 순서 동일하게 호출. 일치.
- `nameMap[i]`의 `i`는 숫자, 맵 키는 `s.id`(숫자) → JS 객체 키로는 둘 다 `"1"`로 정규화되므로 조회된다.

# 아침칠판 날씨 자동 입력 + 안전수칙 확장 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 아침칠판 안전수칙을 월별 31개로 늘려 한 달 내 반복을 없애고, 설정에서 고른 지역의 날씨를 아침 자동 채우기 때 날짜 뒤에 붙인다.

**Architecture:** 안전수칙은 상수 `SAFETY_BY_MONTH`를 교체하는 순수 데이터 변경이다(선택 로직 `getSafetyMsg`는 이미 풀 길이로 나누므로 무수정). 날씨는 Open-Meteo(키 불필요·CORS 허용)를 쓰되, 지오코딩 정확도가 낮아 검색 결과를 자동 채택하지 않고 시·도를 함께 보여준 뒤 선생님이 고른 좌표를 반 설정에 저장한다. 조회는 `autoFillDashboard`에서 하루 한 번만 하고, 실패하면 조용히 날짜만 넣는다.

**Tech Stack:** 단일 파일 `index.html` (바닐라 JS + Firebase RTDB 8.10.1). 빌드 도구 없음. 테스트는 `tests/roster-names.test.js`와 같은 방식의 의존성 없는 Node 스크립트.

## Global Constraints

- **날씨는 부가 기능이다. 어떤 실패도 칠판 자동 채우기를 막아선 안 된다.** 지역 미설정·네트워크 오류·타임아웃·알 수 없는 코드 → 전부 날짜만 넣고 조용히 진행.
- 날씨 조회 타임아웃은 **5초**.
- 날씨는 **`autoFillDashboard`에서만** 조회한다. 주기적 갱신·페이지 로드마다 갱신 금지 — 선생님이 손으로 고친 내용을 덮어쓰면 안 된다.
- 지오코딩 결과를 **자동 채택하지 않는다.** 반드시 후보 목록에 `이름 · 시·도`를 표시하고 선생님이 클릭해 고르게 한다. (`천안` 검색 시 강원도가 1순위로 나오는 것이 실측 확인됨)
- 좌표 기본값: **아산시(충청남도) `36.78361`, `127.00417`**. 기본값 사용 중일 때는 설정 화면에 `— 기본값`을 표시한다.
- `getSafetyMsg`는 **수정하지 않는다.**
- `rpgStudentInit()`, `nsParseRoster()`, `rpgParseRosterStr()`, `firebase-rules.json`은 **수정하지 않는다.**
- 저장 위치는 `settings/dashboardDefaults`의 `weatherLat`(number) / `weatherLon`(number) / `weatherPlace`(string). 이 노드는 무인증 공개이므로 **학생 이름을 넣지 않는다.**
- 사용자 입력이 화면에 들어갈 때는 `escapeHtml()`을 거친다.
- **Task 2까지 끝난 뒤 한 번, Task 5까지 끝난 뒤 한 번만 푸시한다.** 푸시하면 선생님이 매일 쓰는 라이브 사이트에 즉시 배포된다.

## File Structure

| 파일 | 역할 | 변경 |
|---|---|---|
| `index.html` | 앱 전체 (단일 파일, 레포 관행) | 수정 |
| `docs/superpowers/plans/2026-07-29-safety-messages.js` | 안전수칙 372개 원본 데이터 (이미 작성·검증 완료) | 참조만 |
| `tests/weather-safety.test.js` | 날씨·안전수칙 단위 테스트 (Node, 무의존성) | 신규 |

---

### Task 1: 안전수칙 12개월 × 31개로 교체

순수 데이터 변경이다. 로직은 건드리지 않는다.

**Files:**
- Modify: `index.html` — `const SAFETY_BY_MONTH = {` 부터 짝이 맞는 `};` 까지 전체
- Create: `tests/weather-safety.test.js`

**Interfaces:**
- Consumes: `getSafetyMsg(d)` (기존, 수정 금지) — `pool[(d.getDate()-1) % pool.length]`
- Produces: 없음 (데이터만)

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/weather-safety.test.js` 생성:

```js
// 의존성 없는 테스트. 실행: node tests/weather-safety.test.js
const fs = require('fs');
const path = require('path');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

// index.html에서 SAFETY_BY_MONTH 객체 리터럴을 중괄호 짝으로 잘라낸다.
function extractSafety() {
  const key = 'const SAFETY_BY_MONTH = ';
  const start = SRC.indexOf(key);
  if (start < 0) throw new Error('SAFETY_BY_MONTH를 찾을 수 없음');
  let depth = 0, began = false;
  for (let j = SRC.indexOf('{', start); j < SRC.length; j++) {
    if (SRC[j] === '{') { depth++; began = true; }
    else if (SRC[j] === '}') { depth--; if (began && depth === 0) return eval('(' + SRC.slice(SRC.indexOf('{', start), j + 1) + ')'); }
  }
  throw new Error('닫는 중괄호를 못 찾음');
}

let pass = 0, fail = 0;
function ok(label, cond, detail) {
  if (cond) { pass++; console.log('  ok   ' + label); }
  else { fail++; console.log('  FAIL ' + label + (detail ? '\n       ' + detail : '')); }
}

console.log('SAFETY_BY_MONTH — 월별 31개, 한 달 안에서 반복 없음');
const S = extractSafety();
for (const m of [1,2,3,4,5,6,7,8,9,10,11,12]) {
  const pool = S[m];
  ok(m + '월이 존재한다', Array.isArray(pool));
  if (!Array.isArray(pool)) continue;
  ok(m + '월이 31개다', pool.length === 31, '실제 ' + pool.length + '개');
  const dup = pool.filter((x, i) => pool.indexOf(x) !== i);
  ok(m + '월 안에 같은 문구가 없다', dup.length === 0, dup.join(' / '));
  ok(m + '월 문구가 모두 비어있지 않다', pool.every(t => typeof t === 'string' && t.trim().length > 0));
}

// 한 달 31일 전부 서로 다른 문구가 나와야 한다 (예전엔 9일마다 반복됐다)
console.log('getSafetyMsg 방식 — 같은 달 31일이 모두 다른 문구');
for (const m of [1,3,7,9,12]) {
  const pool = S[m];
  const seen = [];
  for (let d = 1; d <= 31; d++) seen.push(pool[(d - 1) % pool.length]);
  const dup = seen.filter((x, i) => seen.indexOf(x) !== i);
  ok(m + '월 1~31일 문구가 모두 다르다', dup.length === 0, dup.join(' / '));
}

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

실행: `node tests/weather-safety.test.js`
기대: `FAIL  1월이 31개다   실제 9개` 형태로 여러 건 실패, 종료 코드 1

- [ ] **Step 3: 데이터 교체**

`docs/superpowers/plans/2026-07-29-safety-messages.js` 파일을 연다. 그 파일의
`const SAFETY_BY_MONTH = {` 부터 마지막 `};` 까지를 **그대로 복사**해서,
`index.html`의 기존 `const SAFETY_BY_MONTH = { ... };` 블록을 **통째로 교체**한다.

주의사항:
- 원본 파일 맨 위 `//` 주석 4줄은 **복사하지 않는다.**
- `index.html` 안에서의 들여쓰기(공백 8칸)를 유지한다.
- 월 순서는 원본 그대로 `3,4,5,6,7,8,9,10,11,12,1,2` 이다. 재정렬하지 않는다.
- 기존 블록의 앞뒤 코드(`// 🛟 달별 안전 수칙...` 주석과 `function getSafetyMsg`)는 건드리지 않는다.

- [ ] **Step 4: 테스트 통과 확인**

실행: `node tests/weather-safety.test.js`
기대: `41 passed, 0 failed`

- [ ] **Step 5: 문법 검사**

실행:

```bash
node -e "const fs=require('fs'),vm=require('vm');const s=fs.readFileSync('index.html','utf8');const m=s.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/);new vm.Script(m[1]);console.log('문법 OK');"
```

기대: `문법 OK`

- [ ] **Step 6: 기존 테스트 회귀 확인**

실행: `node tests/roster-names.test.js`
기대: `16 passed, 0 failed`

- [ ] **Step 7: 커밋**

```bash
git add index.html tests/weather-safety.test.js
git commit -m "안전수칙을 월별 31개로 확장 (한 달 내 반복 제거)"
```

---

### Task 2: 안전수칙 배포

Task 1은 데이터 변경뿐이라 위험이 낮다. 날씨 작업과 분리해 먼저 배포한다.

**Files:** 없음 (배포만)

**Interfaces:** 없음

- [ ] **Step 1: 푸시**

```bash
git push origin main
```

- [ ] **Step 2: 배포 반영 확인**

실행:

```bash
curl -s "https://doedo81.github.io/sinli2655/index.html?cb=s1" | grep -c "구명조끼는 물놀이의 기본"
```

기대: `1`. `0`이면 GitHub Pages 빌드를 1~2분 더 기다렸다 재확인한다.

---

### Task 3: 날씨 변환·조회 함수

DOM과 Firebase에 의존하지 않는 부분을 먼저 만들어 단위 테스트한다.

**Files:**
- Modify: `index.html` — `function getSafetyMsg(d) {` 정의 **바로 앞**에 삽입
- Modify: `tests/weather-safety.test.js` — 테스트 추가

**Interfaces:**
- Consumes: 없음
- Produces:
  - `weatherCodeText(code: number) → string` — 예: `0` → `"☀️ 맑음"`, 알 수 없는 코드 → `""`
  - `fetchWeatherText(lat: number, lon: number) → Promise<string>` — 예: `"☀️ 맑음 28℃"`, 실패 시 `""`
  - `WEATHER_DEFAULT` — `{ lat: 36.78361, lon: 127.00417, place: '아산시 (충청남도)' }`

- [ ] **Step 1: 실패하는 테스트 추가**

`tests/weather-safety.test.js`의 `console.log('\n' + pass + ...)` 줄 **바로 앞**에 추가:

```js
console.log('weatherCodeText — WMO 코드를 초등학생이 읽을 표현으로');
const wsrc = SRC.slice(SRC.indexOf('function weatherCodeText'));
let d2 = 0, b2 = false, wfn = '';
for (let j = wsrc.indexOf('{'); j < wsrc.length; j++) {
  if (wsrc[j] === '{') { d2++; b2 = true; }
  else if (wsrc[j] === '}') { d2--; if (b2 && d2 === 0) { wfn = wsrc.slice(0, j + 1); break; } }
}
eval(wfn);
ok('0 → 맑음', weatherCodeText(0) === '☀️ 맑음', weatherCodeText(0));
ok('1 → 대체로 맑음', weatherCodeText(1) === '🌤️ 대체로 맑음', weatherCodeText(1));
ok('2 → 구름 조금', weatherCodeText(2) === '⛅ 구름 조금', weatherCodeText(2));
ok('3 → 흐림', weatherCodeText(3) === '☁️ 흐림', weatherCodeText(3));
ok('45 → 안개', weatherCodeText(45) === '🌫️ 안개', weatherCodeText(45));
ok('48 → 안개', weatherCodeText(48) === '🌫️ 안개', weatherCodeText(48));
ok('53 → 이슬비', weatherCodeText(53) === '🌦️ 이슬비', weatherCodeText(53));
ok('57 → 언 이슬비', weatherCodeText(57) === '🌧️ 언 이슬비', weatherCodeText(57));
ok('63 → 비', weatherCodeText(63) === '🌧️ 비', weatherCodeText(63));
ok('67 → 언 비', weatherCodeText(67) === '🌧️ 언 비', weatherCodeText(67));
ok('73 → 눈', weatherCodeText(73) === '❄️ 눈', weatherCodeText(73));
ok('77 → 싸락눈', weatherCodeText(77) === '🌨️ 싸락눈', weatherCodeText(77));
ok('81 → 소나기', weatherCodeText(81) === '🌦️ 소나기', weatherCodeText(81));
ok('86 → 소나기눈', weatherCodeText(86) === '🌨️ 소나기눈', weatherCodeText(86));
ok('95 → 천둥번개', weatherCodeText(95) === '⛈️ 천둥번개', weatherCodeText(95));
ok('99 → 우박·천둥번개', weatherCodeText(99) === '⛈️ 우박·천둥번개', weatherCodeText(99));
ok('알 수 없는 코드 4 → 빈 문자열', weatherCodeText(4) === '', weatherCodeText(4));
ok('알 수 없는 코드 100 → 빈 문자열', weatherCodeText(100) === '', weatherCodeText(100));
ok('undefined → 빈 문자열', weatherCodeText(undefined) === '', String(weatherCodeText(undefined)));
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

실행: `node tests/weather-safety.test.js`
기대: `weatherCodeText`를 못 찾아 예외로 종료 (`ReferenceError` 또는 슬라이스 실패)

- [ ] **Step 3: 구현 추가**

`index.html`에서 `function getSafetyMsg(d) {` 정의 **바로 앞**에 삽입:

```js
        // 🌤️ 날씨 — 지역이 설정되지 않았을 때 쓰는 기본 좌표 (실측 검증: 충남 아산시)
        const WEATHER_DEFAULT = { lat: 36.78361, lon: 127.00417, place: '아산시 (충청남도)' };

        // WMO 날씨 코드를 초등학생이 읽을 표현으로. 모르는 코드는 빈 문자열(= 날씨 생략).
        function weatherCodeText(code) {
            var t = {
                0: '☀️ 맑음', 1: '🌤️ 대체로 맑음', 2: '⛅ 구름 조금', 3: '☁️ 흐림',
                45: '🌫️ 안개', 48: '🌫️ 안개',
                51: '🌦️ 이슬비', 53: '🌦️ 이슬비', 55: '🌦️ 이슬비',
                56: '🌧️ 언 이슬비', 57: '🌧️ 언 이슬비',
                61: '🌧️ 비', 63: '🌧️ 비', 65: '🌧️ 비',
                66: '🌧️ 언 비', 67: '🌧️ 언 비',
                71: '❄️ 눈', 73: '❄️ 눈', 75: '❄️ 눈', 77: '🌨️ 싸락눈',
                80: '🌦️ 소나기', 81: '🌦️ 소나기', 82: '🌦️ 소나기',
                85: '🌨️ 소나기눈', 86: '🌨️ 소나기눈',
                95: '⛈️ 천둥번개', 96: '⛈️ 우박·천둥번개', 99: '⛈️ 우박·천둥번개'
            };
            return t[code] || '';
        }

        // 현재 날씨 한 줄을 만든다. 실패하면 빈 문자열 — 칠판 채우기를 절대 막지 않는다.
        function fetchWeatherText(lat, lon) {
            if (typeof lat !== 'number' || typeof lon !== 'number') return Promise.resolve('');
            var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + lat + '&longitude=' + lon
                    + '&current=temperature_2m,weather_code&timezone=Asia%2FSeoul';
            var timer;
            var timeout = new Promise(function(resolve) { timer = setTimeout(function(){ resolve(null); }, 5000); });
            return Promise.race([fetch(url).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; }), timeout])
                .then(function(j) {
                    clearTimeout(timer);
                    if (!j || !j.current) return '';
                    var label = weatherCodeText(j.current.weather_code);
                    if (!label) return '';
                    var temp = j.current.temperature_2m;
                    return (typeof temp === 'number') ? (label + ' ' + Math.round(temp) + '℃') : label;
                })
                .catch(function() { clearTimeout(timer); return ''; });
        }

```

- [ ] **Step 4: 테스트 통과 확인**

실행: `node tests/weather-safety.test.js`
기대: `60 passed, 0 failed`

- [ ] **Step 5: 커밋**

```bash
git add index.html tests/weather-safety.test.js
git commit -m "날씨 코드 변환·조회 함수 추가 (Open-Meteo, 5초 타임아웃)"
```

---

### Task 4: 설정에 학교 지역 선택 UI

**Files:**
- Modify: `index.html` — 설정 모달 (`총 학생 수` 입력 줄이 든 `<div>` 바로 뒤)
- Modify: `index.html` — `openSettingsModal`, `saveSettingsData`
- Modify: `index.html` — `weatherCodeText` 정의 뒤에 검색 함수 추가

**Interfaces:**
- Consumes: `WEATHER_DEFAULT`, `escapeHtml(s)`
- Produces:
  - `weatherSearchPlace()` — 입력값으로 지오코딩 후 후보 렌더 (전역, `onclick`에서 호출)
  - `weatherPickPlace(lat, lon, place)` — 후보 클릭 시 선택 상태 반영 (전역)
  - 전역 변수 `pendingWeather` — `{lat, lon, place}` 또는 `null`

- [ ] **Step 1: 설정 모달에 UI 추가**

찾을 코드:

```html
                        <div style="font-weight:bold; color:var(--dark-blue);">총 학생 수: <input type="number" id="set-total-students" value="24" class="setting-input" style="width:80px;">명</div>
                    </div>
```

바꿀 코드 (닫는 `</div>` 뒤에 블록 추가):

```html
                        <div style="font-weight:bold; color:var(--dark-blue);">총 학생 수: <input type="number" id="set-total-students" value="24" class="setting-input" style="width:80px;">명</div>
                    </div>

                    <div style="margin-bottom:15px;">
                        <div style="font-weight:bold; color:var(--dark-blue); font-size:14px;">📍 학교 지역 (아침칠판 날씨용)</div>
                        <p style="font-size:12px; color:#555; margin:5px 0;">시·군까지 붙여서 검색하세요 (예: 아산시). 후보에서 <b>시·도를 확인하고</b> 골라야 정확합니다.</p>
                        <div style="display:flex; gap:6px; align-items:center;">
                            <input type="text" id="set-weather-query" placeholder="예: 아산시" style="flex:1; max-width:220px; padding:8px; border-radius:8px; border:1px solid #ccc; font-family:'Pretendard';" onkeypress="if(event.key==='Enter'){event.preventDefault();weatherSearchPlace();}">
                            <button class="reset-btn" style="padding:8px 14px; font-size:13px;" onclick="weatherSearchPlace()">찾기</button>
                        </div>
                        <div id="weather-search-results" style="margin-top:8px;"></div>
                        <div id="weather-current-label" style="margin-top:6px; font-size:13px; color:#00695c; font-weight:700;"></div>
                    </div>
```

- [ ] **Step 2: 검색·선택 함수 추가**

`index.html`에서 Task 3에 추가한 `function fetchWeatherText(lat, lon) { ... }` 블록 **바로 뒤**에 삽입:

```js
        // 설정에서 고르는 중인 지역 (저장 버튼을 눌러야 실제로 저장된다)
        var pendingWeather = null;

        // 지오코딩은 정확도가 낮다(예: '천안' → 강원도). 그래서 자동 채택하지 않고
        // 시·도를 함께 보여준 뒤 선생님이 직접 고르게 한다.
        function weatherSearchPlace() {
            var box = document.getElementById('weather-search-results');
            var q = (document.getElementById('set-weather-query').value || '').trim();
            if (!q) { box.innerHTML = '<span style="font-size:12px; color:#c62828;">지역명을 입력해 주세요.</span>'; return; }
            box.innerHTML = '<span style="font-size:12px; color:#888;">찾는 중…</span>';
            var url = 'https://geocoding-api.open-meteo.com/v1/search?name=' + encodeURIComponent(q) + '&count=5&language=ko&format=json';
            fetch(url).then(function(r){ return r.ok ? r.json() : null; }).then(function(j) {
                var list = (j && j.results) || [];
                if (!list.length) {
                    box.innerHTML = '<span style="font-size:12px; color:#c62828;">결과가 없어요. 시·군까지 붙여보세요 (예: 아산시)</span>';
                    return;
                }
                box.innerHTML = list.map(function(r) {
                    var place = r.name + (r.admin1 ? ' · ' + r.admin1 : '');
                    return '<button class="reset-btn" style="display:block; width:100%; text-align:left; margin-bottom:4px; padding:8px 10px; font-size:13px; background:#f4f7fb; color:#37474f; box-shadow:none;"'
                         + ' onclick="weatherPickPlace(' + r.latitude + ',' + r.longitude + ',\'' + escapeHtml(place).replace(/'/g, '') + '\')">'
                         + escapeHtml(place) + '</button>';
                }).join('');
            }).catch(function() {
                box.innerHTML = '<span style="font-size:12px; color:#c62828;">검색에 실패했어요. 잠시 후 다시 시도해 주세요.</span>';
            });
        }

        function weatherPickPlace(lat, lon, place) {
            pendingWeather = { lat: lat, lon: lon, place: place };
            document.getElementById('weather-search-results').innerHTML = '';
            document.getElementById('weather-current-label').innerText = '현재 설정: ' + place + ' (저장 버튼을 눌러야 반영돼요)';
        }

```

- [ ] **Step 3: openSettingsModal에서 저장된 지역 표시**

찾을 코드:

```js
                document.getElementById('set-separated-pairs').value = d.separatedPairs || "";
```

바꿀 코드:

```js
                document.getElementById('set-separated-pairs').value = d.separatedPairs || "";
                pendingWeather = null;
                document.getElementById('set-weather-query').value = '';
                document.getElementById('weather-search-results').innerHTML = '';
                document.getElementById('weather-current-label').innerText = d.weatherPlace
                    ? ('현재 설정: ' + d.weatherPlace)
                    : ('현재 설정: ' + WEATHER_DEFAULT.place + ' — 기본값');
```

- [ ] **Step 4: saveSettingsData에서 저장**

찾을 코드:

```js
                roster: rosterStripNames(rosterRaw),
```

바꿀 코드:

```js
                roster: rosterStripNames(rosterRaw),
                weatherLat: pendingWeather ? pendingWeather.lat : (typeof globalWeatherLat === 'number' ? globalWeatherLat : null),
                weatherLon: pendingWeather ? pendingWeather.lon : (typeof globalWeatherLon === 'number' ? globalWeatherLon : null),
                weatherPlace: pendingWeather ? pendingWeather.place : (globalWeatherPlace || null),
```

- [ ] **Step 5: 전역 변수 선언과 로드**

`index.html`에서 찾을 코드:

```js
        let globalStudentRosterStr = "";
```

바꿀 코드:

```js
        let globalStudentRosterStr = "";
        let globalWeatherLat = null, globalWeatherLon = null, globalWeatherPlace = "";
```

이어서 `enterRoom`의 설정 로드에서 찾을 코드:

```js
                    globalStudentRosterStr = savedNames || s.roster || "";
```

바꿀 코드:

```js
                    globalStudentRosterStr = savedNames || s.roster || "";
                    globalWeatherLat = (typeof s.weatherLat === 'number') ? s.weatherLat : null;
                    globalWeatherLon = (typeof s.weatherLon === 'number') ? s.weatherLon : null;
                    globalWeatherPlace = s.weatherPlace || "";
```

- [ ] **Step 6: 문법 검사와 회귀**

실행:

```bash
node -e "const fs=require('fs'),vm=require('vm');const s=fs.readFileSync('index.html','utf8');const m=s.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/);new vm.Script(m[1]);console.log('문법 OK');"
node tests/weather-safety.test.js
node tests/roster-names.test.js
```

기대: `문법 OK`, `60 passed, 0 failed`, `16 passed, 0 failed`

- [ ] **Step 7: 커밋**

```bash
git add index.html
git commit -m "설정에 학교 지역 선택 UI 추가 (검색 후 시·도 확인하고 직접 선택)"
```

---

### Task 5: 아침칠판 자동 채우기에 날씨 붙이기

**Files:**
- Modify: `index.html` — `autoFillDashboard`의 날짜 설정 줄

**Interfaces:**
- Consumes: `fetchWeatherText(lat, lon)`, `WEATHER_DEFAULT`, `globalWeatherLat/Lon`

- [ ] **Step 1: 날짜 뒤에 날씨 붙이기**

찾을 코드:

```js
                document.getElementById('view-date').innerText = `${viewDate.getMonth()+1}월 ${viewDate.getDate()}일 ${dayStr}요일`;
```

바꿀 코드:

```js
                const baseDateText = `${viewDate.getMonth()+1}월 ${viewDate.getDate()}일 ${dayStr}요일`;
                document.getElementById('view-date').innerText = baseDateText;
                // 날씨는 부가 기능 — 늦거나 실패해도 나머지 채우기를 막지 않는다.
                const wLat = (typeof globalWeatherLat === 'number') ? globalWeatherLat : WEATHER_DEFAULT.lat;
                const wLon = (typeof globalWeatherLon === 'number') ? globalWeatherLon : WEATHER_DEFAULT.lon;
                fetchWeatherText(wLat, wLon).then(function(w) {
                    if (!w) return;
                    const el = document.getElementById('view-date');
                    // 그 사이 선생님이 직접 고쳤다면 덮어쓰지 않는다.
                    if (el.innerText !== baseDateText) return;
                    el.innerText = baseDateText + '  ' + w;
                    saveDashboard(true);
                });
```

- [ ] **Step 2: 문법 검사와 회귀**

실행:

```bash
node -e "const fs=require('fs'),vm=require('vm');const s=fs.readFileSync('index.html','utf8');const m=s.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/);new vm.Script(m[1]);console.log('문법 OK');"
node tests/weather-safety.test.js
node tests/roster-names.test.js
```

기대: `문법 OK`, `60 passed, 0 failed`, `16 passed, 0 failed`

- [ ] **Step 3: 커밋**

```bash
git add index.html
git commit -m "아침칠판 자동 채우기에 날씨 붙이기 (실패 시 날짜만)"
```

---

### Task 6: 통합 검증 후 배포

**Files:** 없음 (검증·배포만)

- [ ] **Step 1: 로컬 서버 기동**

```bash
py -3 -m http.server 8791
```

브라우저에서 **`http://localhost:8791/index.html`** 을 연다.
(`127.0.0.1`은 Firebase 인증 허용 도메인이 아니라 로그인이 안 된다. 반드시 `localhost`)

- [ ] **Step 2: 지역 미설정 상태 확인**

설정을 열어 `현재 설정: 아산시 (충청남도) — 기본값`이 보이는지 확인한다.
아침칠판에서 `🔄 자동 채우기`를 눌러 날짜 뒤에 `☀️ 맑음 30℃` 형태가 붙는지 본다.

- [ ] **Step 3: 지역 검색·선택 확인**

설정에서 `천안`으로 검색한다. 후보에 `천안 · 강원도`가 나오는지 확인한다 —
**이것이 시·도를 함께 보여줘야 하는 이유다.** 이어서 `천안시`로 검색해 `천안시 · 충청남도`를
고르고 저장한 뒤, 설정을 다시 열어 `현재 설정: 천안시 · 충청남도`(기본값 표시 없음)가
보이는지 확인한다. 확인 후 `아산시`로 되돌려 저장한다.

- [ ] **Step 4: 네트워크 차단 상태 확인 (가장 중요)**

브라우저 F12 → Network 탭 → `Offline` 체크. 그 상태에서 아침칠판 `🔄 자동 채우기`를 누른다.

기대: **날짜·시간표·당번·안전수칙이 정상적으로 채워지고, 날씨만 빠진다.** 5초 안에 끝나야 한다.
칠판이 비거나 멈추면 여기서 중단하고 원인을 찾는다. 절대 푸시하지 않는다.

확인 후 `Offline` 체크를 해제한다.

- [ ] **Step 5: 안전수칙 반복 확인**

아침칠판에서 달력의 날짜를 1일 → 10일 → 19일 → 28일로 바꿔 가며 `🛟 안전 수칙` 칸이
**매번 다른 문구**로 바뀌는지 확인한다. (예전에는 이 네 날짜가 모두 같았다)

- [ ] **Step 6: 푸시**

```bash
git push origin main
```

- [ ] **Step 7: 배포 반영 확인**

```bash
curl -s "https://doedo81.github.io/sinli2655/index.html?cb=w1" | grep -c "weatherCodeText"
```

기대: `1` 이상. `0`이면 1~2분 더 기다렸다 재확인한다.

- [ ] **Step 8: 공개 노드에 이름이 없는지 재확인**

```bash
curl -s "https://classscore-sinli-default-rtdb.firebaseio.com/rooms/%EC%8B%A0%EB%A6%AC%EC%B4%885%ED%95%99%EB%85%845%EB%B0%98/settings/dashboardDefaults.json" | head -c 400
```

기대: `weatherLat`, `weatherLon`, `weatherPlace`, 번호+성별만 있는 `roster`가 보이고
**학생 이름은 없어야 한다.**

---

## Self-Review

**Spec coverage:**

| 스펙 항목 | 담당 Task |
|---|---|
| 위치를 설정에서 직접 고른다 (자동 채택 금지, 시·도 표시) | Task 4 Step 1·2 |
| 좌표·지명을 `weatherLat/Lon/Place`에 저장 | Task 4 Step 4·5 |
| 기본값 아산시 + `— 기본값` 표시 | Task 3 Step 3(상수), Task 4 Step 3 |
| 아침 자동 채우기 때만 한 번 조회 | Task 5 Step 1 |
| 선생님이 고친 내용 덮어쓰지 않음 | Task 5 Step 1 (`el.innerText !== baseDateText` 가드) |
| WMO 코드 → 한글 변환표 전체 | Task 3 Step 3 |
| 실패·미설정·타임아웃 시 날짜만 | Task 3 Step 3, Task 5 Step 1, Task 6 Step 4 |
| 타임아웃 5초 | Task 3 Step 3 |
| 안전수칙 월별 31개 | Task 1 |
| `getSafetyMsg` 무수정 | Global Constraints (명시적 금지) |
| 안전수칙 먼저 배포, 날씨 나중 | Task 2(안전수칙 배포), Task 6(날씨 배포) |
| 공개 노드에 학생 이름 없음 | Task 6 Step 8 |

빠진 항목 없음.

**Placeholder scan:** TBD/TODO/"적절히 처리" 없음. 모든 코드 단계에 찾을 코드/바꿀 코드를 전문으로 적었다. 안전수칙 372개는 `docs/superpowers/plans/2026-07-29-safety-messages.js`에 실제 데이터로 존재하며, 12개월 × 31개·월내 중복 없음을 이미 검증했다.

**Type consistency:**
- `weatherCodeText(code) → string` — Task 3 정의, 같은 Task 테스트와 `fetchWeatherText`에서 사용. 일치.
- `fetchWeatherText(lat, lon) → Promise<string>` — Task 3 정의, Task 5에서 `.then(function(w){...})`로 소비. 일치.
- `WEATHER_DEFAULT = {lat, lon, place}` — Task 3 정의, Task 4 Step 3·Task 5 Step 1에서 `.place`/`.lat`/`.lon` 접근. 일치.
- `pendingWeather = {lat, lon, place} | null` — Task 4 Step 2 정의, 같은 Task Step 3·4에서 사용. 일치.
- `globalWeatherLat/Lon/Place` — Task 4 Step 5 선언·로드, Task 4 Step 4·Task 5 Step 1에서 읽음. 일치.
- `weatherPickPlace(lat, lon, place)` — Task 4 Step 2 정의, 같은 Step의 `onclick` 문자열에서 3인자로 호출. 일치.

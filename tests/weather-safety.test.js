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

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);

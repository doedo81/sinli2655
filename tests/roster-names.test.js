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
  extractFn('escapeHtml'),
  extractFn('rpgParseRosterStr'),
  extractFn('rosterStripNames'),
  extractFn('rosterNameMapFrom'),
  extractFn('hwStudentBtnHtml'),
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

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);

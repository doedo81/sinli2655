# CLAUDE.md

이 파일은 [Claude Code](https://claude.com/claude-code)를 비롯한 AI 어시스턴트가 이 저장소에서 작업할 때 참고하는 안내서입니다.

## 프로젝트 개요

**아침칠판 + 성장 시스템** — 초등 교사용 학급 운영 웹앱입니다. 아침칠판(오늘의 시간표·안내·급훈), 캘린더, 모둠 점수판, 활동/뽑기 도구, 과제 관리, 자리 배치, RPG형 성장(상벌점) 시스템을 하나의 화면에서 제공합니다. 여러 교사가 각자 학급을 만들어 쓰는 다중 학급·다중 교사 구조로 개편 중입니다.

- **대상 사용자**: 초등 교사(담임/전담)와 학생(태블릿·핸드폰 열람)
- **언어**: UI·코드 주석·문서·커밋 메시지 모두 **한국어**. 새로 작성하는 것도 한국어로 맞춰 주세요.
- **배포**: GitHub Pages (정적 호스팅). `git push` 후 30~60초면 실제 사이트에 반영됩니다.

## 기술 스택 · 아키텍처

이 앱은 **빌드 도구·프레임워크·패키지 매니저가 없는 순수 정적 사이트**입니다. `npm`, 번들러, 트랜스파일러가 없습니다.

- **프런트엔드**: 단일 파일 `index.html` (약 5,400줄, ~450KB) 안에 HTML·CSS·바닐라 JavaScript가 모두 들어 있습니다. `<script>` 태그 하나에 전역 함수들이 정의된 구조입니다.
- **백엔드**: Firebase (CDN v8.10.1, compat API)
  - **Realtime Database** — 모든 앱 데이터 저장 (`db.ref(...)`)
  - **Auth** — 교사는 구글 로그인 / 이메일 로그인, 학생은 방번호+비밀번호 간편 로그인
  - Firebase 프로젝트: `classscore-sinli` (설정은 `index.html`의 `firebaseConfig` 참고)
- **외부 CDN**: Pretendard 폰트, Font Awesome 6.5.1, 효과음(mixkit), QR 생성(api.qrserver.com). WebAudio로 합성한 효과음도 있음.
- **선택적 AI 기능**: 캘린더 일정 자동 추출(`aiExtractEvents`)에 Google Gemini API 사용. API 키는 사용자가 설정 모달에 입력하며 `localStorage`(`geminiApiKey`)에만 저장됨.

### 파일 구조

```
index.html                     # 앱 전체 (HTML+CSS+JS). 거의 모든 작업이 여기서 이뤄짐
firebase-rules.json            # Firebase RTDB 보안 규칙 (콘솔에 수동 붙여넣기)
.nojekyll                      # GitHub Pages가 Jekyll 처리를 건너뛰게 함
.gitignore
assets/
  avatars/                     # 직업×성별 캐릭터 이미지 (knight_m.png 등), CREDITS.txt
  items/head/                  # 머리 장식 아이템 (crown, halo, star ...)
  items/pet/                   # 펫 아이템 (cat, dragon, egg ...)
  lpc/, avatars/_layers/       # (.gitignore 처리됨 — 원본 소스, 커밋 안 함)
성장시스템_기획서.md            # RPG 성장 시스템 상세 기획 (능력치·직업·XP·경고게이지)
아키텍처_다중학급_설계.md        # 다중 학급/교사 데이터 모델·권한·로드맵
파이어베이스_보안규칙_적용.md     # 보안 규칙 적용/롤백 가이드
```

## `index.html` 내부 구조

전부 한 파일이므로, 편집 전에 관련 영역을 `grep`으로 먼저 찾는 것이 좋습니다.

- **`<head>` (1~1317줄 부근)**: CDN 링크 + 대부분의 CSS. 디자인 테마는 CSS 변수(`:root`의 `--main-sky`, `--accent-blue` 등 파스텔 스카이 톤)로 관리.
- **`<body>` 마크업 (~1318줄 이전)**: `#auth-overlay`(로그인), `.sidebar`(탭 버튼), `.content-section` 7개 탭.
- **`<script>` (~1318줄 이후 끝까지)**: 전역 함수 정의. `onclick="함수명(...)"` 인라인 핸들러로 HTML과 연결.

### 탭(화면) 구성 — `switchTab(t)`로 전환

| 탭 id | 이름 | 주요 함수 접두어 |
|---|---|---|
| `board` | 🗒️ 아침 칠판 (시간표·안내·급훈·당번) | `saveDashboard`, `autoFillDashboard`, `loadTodayBoard`, `tt*` |
| `calendar` | 🗓️ 캘린더 | `renderCalendar*`, `openDayPopover`, `aiExtractEvents` |
| `score` | ⭐ 모둠 점수판 | `changeScore`, `buildScoreboardHTML`, `updateRankings` |
| `picker` | 🎲 활동 & 뽑기 (타이머·모둠뽑기·학생뽑기·미니칠판 위젯) | `act*`, `drawGroupCard`, `drawStudentCard` |
| `homework` | 📚 과제 관리 | `addHomework`, `renderHomeworkList`, `cycleH` |
| `seating` | 🪑 자리 배치 (스마트/랜덤/협동/성장 정렬) | `ns*` (신규 엔진), `renderSeatingGrid`, `generateSmartSeating` |
| `rpg` | 🐉 성장 (상벌점) | `rpg*` — 가장 큰 모듈 |

### 함수 네이밍 규칙 (중요)

파일이 한 스코프에 있어 함수가 매우 많습니다. **접두어로 모듈을 구분**합니다. 새 함수는 해당 접두어 규칙을 따르세요.

- `rpg*` — 성장 시스템 (학생 카드, 레벨/XP, 능력치, 직업, 경고 게이지, 아바타 꾸미기, 미션)
- `ns*` — 자리 배치 v2 엔진 ("new seating": 명단 파싱, 짝/모둠 편성, 회피 규칙, 뷰 렌더)
- `act*` — 활동/뽑기 탭의 캔버스·위젯 (미니 칠판 필기, 위젯형 타이머·점수·뽑기)
- `class*` / `enterRoom` / `enterClassById` / `createClass` / `joinClassByCode` — 학급 신원·입장·관리
- `tt*` — 시간표(timetable) 편집
- `cal*` / `day*` — 캘린더
- `gxp*` — 모둠 단위 성장 XP 지급

### 성장(RPG) 시스템 핵심 상수

`index.html` 4158줄 부근에 정의. 값을 바꾸면 게임 밸런스가 바뀝니다.

- `RPG_STATS` — 능력치 6종: 지력(int)·지혜(wis)·체력(str)·민첩(dex)·매력(cha)·정신(mnd)
- `RPG_JOBS` — 직업 5종: 기사·마법사·성직자·궁수·음유시인 (Lv10 전직)
- `RPG_ACTIONS` — 상점(포인트) 편성표: 항목별 `xp`·`stat`·`group`(습관/노력/특별)
- 레벨 곡선: `필요XP = RPG_XP_BASE + (레벨-1) × RPG_XP_STEP` (기본 50 / 30)
- 경고 게이지: 벌점 +20, 60 넘으면 알림, 선행 −10, 매주 월요일 자동 −20

기획 상세는 `성장시스템_기획서.md`를 참고하세요.

## 데이터 모델 (Firebase RTDB)

모든 학급 데이터는 `rooms/<classId>/` 아래에 저장됩니다. `classId`는 자동 생성 고유 키이고, 사람이 쓰는 참여 코드는 별도(`classCodes`)입니다.

```
users/<uid>/                        # 교사별 소속 학급 목록·역할 (본인만 접근)
classCodes/<code>: <classId>        # 교사 학급 참여 코드
studentCodes/<code>: <classId>      # 학생 로그인 코드 (?s=코드)
rooms/<classId>/
  _meta/          { name, ownerUid, code, ... }   # 학급 메타·소유자
  _members/<uid>/ { role, name }                  # 담임(owner)/전담(subject) 멤버
  settings/       dashboardDefaults(roster 명단 포함), groupCount, lastDuty*
  skyDashboard/   # 아침칠판 오늘 내용
  boardHistory/   # 날짜별 칠판 기록
  calendarEvents/ groupScores/ miniScores/ groupTasks/ timerState/
  bookmarks/ homeworks/ seating/ seatingV2/ seatingHistory/ groupMembers/
  rpg/
    config/       { stats, jobs, studentCode, ... }
    students/<번호>/ { name, level, xp, stats{}, job, warning, head, pet, frame, ... }
  rpgArchives/    # 학기말 성장 데이터 보관
```

- **명단은 자리배치용 명단(`settings/dashboardDefaults/roster`)을 재활용** — 성장·자리·뽑기가 같은 명단을 공유합니다. 명단을 새로 만들지 마세요.
- 학생은 자기 캐릭터 꾸미기(머리·펫·프레임·직업)만 쓰기 가능, XP·능력치·점수는 교사만 변경 가능 (보안 규칙으로 강제).

### 권한 모델

- **owner(담임)**: 학급 개설자. 전부 편집 가능.
- **subject(전담)**: 코드로 참여. 성장 점수 주기 + 명단 보기만. 칠판·설정 편집 불가.
- **학생**: `?s=<코드>`로 접속 → 자기 번호+비밀번호(기본 123456) 로그인 → 성장 상태창 열람 + 캐릭터 꾸미기.
- **태블릿 열람 모드**: URL에 `?mode=view` → 사이드바·편집 UI 숨긴 읽기 전용(TV·태블릿 상시 표시용).

## 개발 워크플로

1. **로컬 확인**: 정적 파일이므로 `index.html`을 브라우저로 직접 열거나 간단한 정적 서버로 확인합니다. 단, 구글 로그인·Firebase는 배포 도메인/localhost 승인 도메인에서 동작합니다.
2. **작은 단위로 커밋 → 푸시 → 실제 사이트에서 검증**. 큰 변경일수록 단계를 쪼개고 각 단계마다 검증하세요 (아키텍처 문서 §8 참고).
3. **하위 호환 유지**: 기존 '신리' 반 등 실사용 데이터가 계속 동작하도록 유지합니다. Firebase 스키마를 바꿀 때는 마이그레이션/폴백을 함께 두세요 (`migrateSharedBoard`, `ensureClassOwnership` 등 참고).

### 보안 규칙 변경 시 (매우 중요)

- 보안 규칙은 `firebase-rules.json` 파일에 있으며, **Firebase 콘솔에 사람이 수동으로 붙여넣어 게시**합니다 (이 저장소에서 자동 배포되지 않음).
- 규칙을 바꾸면 반드시 `파이어베이스_보안규칙_적용.md`의 테스트 체크리스트를 따르고, 적용 전 기존 규칙을 백업하세요. 잘못하면 실사용 학급이 "권한 없음"으로 잠길 수 있습니다.
- 규칙은 데이터를 지우지 않고 접근 권한만 정합니다. 문제가 생기면 백업본으로 즉시 롤백 가능.

## 코딩 컨벤션

- **바닐라 JS, 전역 함수, 인라인 `onclick` 핸들러** 스타일을 유지하세요. 프레임워크·모듈·빌드 단계를 새로 도입하지 마세요.
- 새 함수는 위의 **접두어 네이밍 규칙**을 따르고, 관련 기능 근처에 배치하세요.
- CSS는 `<head>`의 기존 스타일과 **CSS 변수(파스텔 스카이 테마)**를 재사용하세요.
- 사용자 입력을 HTML에 넣을 때는 기존 `escapeHtml()`을 사용하세요.
- UI 텍스트·주석·커밋 메시지는 한국어로 작성하고, 기존 커밋 스타일(예: `성장 자리배치(모둠): 한 줄에 3모둠 고정`)을 따르세요.
- Firebase 접근은 `enterRoom()`에서 초기화되는 전역 ref 변수(`boardRef`, `rpgRef`, `scoresRef` 등)를 재사용하고, 필요하면 `db.ref('rooms/' + currentRoom + '/...')` 패턴을 쓰세요.

## Git 규칙

- 개발 브랜치: `claude/claude-md-docs-s6apjh` (지정된 경우). 지정 브랜치 외에는 **명시적 허가 없이 푸시 금지**.
- 푸시는 `git push -u origin <branch>`. 네트워크 오류 시에만 지수 백오프로 재시도.
- **PR은 사용자가 명시적으로 요청할 때만** 생성하세요.

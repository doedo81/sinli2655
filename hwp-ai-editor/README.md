# hwp-ai-editor

한글(HWP/HWPX) 문서를 무손실로 편집하고, 표 레이아웃을 자동으로 맞추는 편집 엔진.
장기적으로 AI가 자연어 명령·양식 준수·규정 검토까지 수행하는 웹 앱으로 확장한다.

기획 배경과 전체 로드맵은 [`기획서_한글AI편집기.md`](./기획서_한글AI편집기.md) 참조.

## 구성

```
hwpxlib/
  core.py       검증된 HWPX 편집 엔진 (기존 hwpx_edit_v7.py, 로직 불변)
                + 웹용 from_bytes() / save_bytes() / replace_regex()
  autotable.py  표 자동 레이아웃 autofit_table()          ★ 핵심
  template.py   표준 양식 준수 편집 apply_template()       ★ 핵심
  hwp_reader.py 구형 .hwp 읽기 (olefile+zlib, 읽기 전용)
  cli.py        하위호환 CLI (기존 명령 + autofit + template + replace-re)
server/
  app.py        무외부의존 웹앱 백엔드 (stdlib http.server)
  ops.py        편집 op 실행기·조회 헬퍼 (수동 UI와 AI가 공유)
  tools.py      Claude tool-use 도구 스키마
  ai_agent.py   자연어 편집 에이전트 (urllib Messages API, 키 미저장)
web/
  index.html    브라우저 SPA (업로드·표 편집·AI 채팅·다운로드)
tests/
  fixtures.py       테스트용 최소 HWPX 생성기
  test_engine.py    회귀 + AutoTable 검증
  test_template.py  양식 준수 편집 검증
  test_replace_regex.py  안전 치환 검증
  test_hwp_reader.py     .hwp 레코드 파서 검증
  test_ai_agent.py       AI tool-use 루프 검증(목 기반)
```

## 웹앱 실행 (설치 불필요)

```bash
cd hwp-ai-editor
python3 -m server.app          # → http://localhost:8000
```

브라우저에서 열고 → `.hwpx` 업로드 → 왼쪽 표 목록에서 표 선택 →
셀 클릭 편집 · 자동맞춤 · 행/열 삭제 · 합계 재계산 · 정규식 바꾸기 · 구조검진 →
⬇ 다운로드. 편집할 때마다 구조검진(verify)이 자동으로 갱신된다.

**구형 `.hwp`도 업로드 가능** — 문단 텍스트를 추출해 읽기 전용으로 보여준다(분석·요약용).
편집하려면 한/글에서 `.hwpx`로 저장 후 업로드. (`.hwp` 읽기는 `pip install olefile` 필요)

## 🤖 AI 자연어 편집 (Claude tool-use)

화면 아래 **AI 편집** 패널에 자연어로 지시하면 Claude가 도구(엔진 op)를 골라
실행하고 `verify`로 자기검증한 뒤 결과를 보고한다. 사람이 행·열·치수를 지정하지
않고 "무엇을 넣을지"만 말한다.

- 예: `"3번 표 모든 과목 20으로 채워줘"`, `"6학년을 5학년으로 바꿔줘"`,
  `"현황표 담임 열 삭제"`, `"표가 몇 개야?"`
- **본인 Claude API 키**를 ⚙ 설정에 입력(브라우저 localStorage에만 저장, 요청마다
  Anthropic으로만 전송 — **서버에 저장·기록하지 않음**). AI 편집은 본인 API 사용량으로 과금.
- 모델 선택(기본 `claude-opus-4-8`, 저비용 `claude-sonnet-5`/`claude-haiku-4-5`).
- **↶ 실행취소** 버튼으로 직전 AI/수동 편집을 되돌린다.

노출 도구: 조회(`list_tables`/`get_table`/`list_paragraphs`) + 편집(`set_cell`/
`autofit`/`del_col`/`del_row`/`del_table`/`copy_row`/`replace_regex`/`sum_row`).
SDK 없이 표준 라이브러리 `urllib`로 Messages API를 직접 호출한다(무외부의존 유지).

## 의존성

- **엔진 본체**(hwpxlib core/autotable/template)와 **웹앱**(server): **표준 라이브러리만** — 설치 0.
- **구형 `.hwp` 읽기**만 선택 의존성 `olefile` 필요: `pip install olefile`.

## CLI 사용법

```bash
# 표/문단 보기
python3 -m hwpxlib.cli 문서.hwpx tables
python3 -m hwpxlib.cli 문서.hwpx list

# 셀 편집
python3 -m hwpxlib.cli 문서.hwpx set-cell 0 1 2 "홍길동" -o 결과.hwpx

# ★ 표 자동 레이아웃 (전체 폭 유지, 긴 내용 열만 넓힘)
python3 -m hwpxlib.cli 문서.hwpx autofit 0 -o 결과.hwpx

# ★ 표준 양식 준수 편집 (채움 칸만, 행 자동 증설 + 자동 맞춤)
python3 -m hwpxlib.cli 양식.hwpx template-info 0
python3 -m hwpxlib.cli 양식.hwpx apply-template 0 --records "홍길동|총무과;이영희|기획과" -o 결과.hwpx

# 구조 검진 (편집 마무리 권장)
python3 -m hwpxlib.cli 문서.hwpx verify
```

전체 명령 목록은 인자 없이 실행하면 나온다: `python3 -m hwpxlib.cli`

## 테스트

```bash
cd hwp-ai-editor
python3 tests/test_engine.py
```

## 라이브러리로 사용

```python
from hwpxlib import HwpxDoc, autofit_table

doc = HwpxDoc.from_bytes(open("문서.hwpx", "rb").read())
doc.set_cell(0, 1, 0, "김철수")     # 표 0, 1행 0열 교체
autofit_table(doc, 0)               # 표 0 자동 레이아웃
open("결과.hwpx", "wb").write(doc.save_bytes())
```

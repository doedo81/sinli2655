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
  cli.py        하위호환 CLI (기존 명령 + autofit + template + replace-re)
server/
  app.py        무외부의존 웹앱 백엔드 (stdlib http.server)
web/
  index.html    브라우저 SPA (업로드·표 편집·다운로드)
tests/
  fixtures.py       테스트용 최소 HWPX 생성기
  test_engine.py    회귀 + AutoTable 검증
  test_template.py  양식 준수 편집 검증
  test_replace_regex.py  안전 치환 검증
```

## 웹앱 실행 (설치 불필요)

```bash
cd hwp-ai-editor
python3 -m server.app          # → http://localhost:8000
```

브라우저에서 열고 → `.hwpx` 업로드 → 왼쪽 표 목록에서 표 선택 →
셀 클릭 편집 · 자동맞춤 · 행/열 삭제 · 합계 재계산 · 정규식 바꾸기 · 구조검진 →
⬇ 다운로드. 편집할 때마다 구조검진(verify)이 자동으로 갱신된다.
(AI 자연어 편집은 다음 단계 — Claude API 연동 예정)

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

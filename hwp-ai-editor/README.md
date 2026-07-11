# hwp-ai-editor

한글(HWP/HWPX) 문서를 무손실로 편집하고, 표 레이아웃을 자동으로 맞추는 편집 엔진.
장기적으로 AI가 자연어 명령·양식 준수·규정 검토까지 수행하는 웹 앱으로 확장한다.

기획 배경과 전체 로드맵은 [`기획서_한글AI편집기.md`](./기획서_한글AI편집기.md) 참조.

## 구성

```
hwpxlib/
  core.py       검증된 HWPX 편집 엔진 (기존 hwpx_edit_v7.py, 로직 불변)
                + 웹용 from_bytes() / save_bytes()
  autotable.py  표 자동 레이아웃 autofit_table()  ★ 핵심
  cli.py        하위호환 CLI (기존 명령 + autofit)
tests/
  fixtures.py   테스트용 최소 HWPX 생성기
  test_engine.py  회귀 + AutoTable 검증
```

## CLI 사용법

```bash
# 표/문단 보기
python3 -m hwpxlib.cli 문서.hwpx tables
python3 -m hwpxlib.cli 문서.hwpx list

# 셀 편집
python3 -m hwpxlib.cli 문서.hwpx set-cell 0 1 2 "홍길동" -o 결과.hwpx

# ★ 표 자동 레이아웃 (전체 폭 유지, 긴 내용 열만 넓힘)
python3 -m hwpxlib.cli 문서.hwpx autofit 0 -o 결과.hwpx

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

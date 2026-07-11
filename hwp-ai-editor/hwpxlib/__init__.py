"""hwpxlib — 한글 HWPX 무손실 편집 엔진 + 표 자동 레이아웃.

기존 hwpx_edit_v7.py의 검증된 HwpxDoc 엔진을 라이브러리로 승격한 패키지.
core: 문단·표·셀·글꼴·구조검진 (로직 불변, 웹용 from_bytes/save_bytes 추가)
autotable: 표 자동 레이아웃 (autofit_table)
"""
from .core import HwpxDoc, GOV_DOC_RULES
from .autotable import autofit_table
from .template import extract_schema, apply_template, validate_template

__all__ = ["HwpxDoc", "GOV_DOC_RULES", "autofit_table",
           "extract_schema", "apply_template", "validate_template",
           "GRADE_REPLACE_PAT"]

# 학년 치환 안전 패턴: '2026학년도'·'5~6학년'·'3~4학년'을 보호하고
# 앞이 숫자/범위기호가 아닐 때만 'N학년'을 매칭 (repl에서 학년 숫자 지정).
GRADE_REPLACE_PAT = r'(?<![0-9~∼·\-])6\s*학년'

"""hwpxlib — 한글 HWPX 무손실 편집 엔진 + 표 자동 레이아웃.

기존 hwpx_edit_v7.py의 검증된 HwpxDoc 엔진을 라이브러리로 승격한 패키지.
core: 문단·표·셀·글꼴·구조검진 (로직 불변, 웹용 from_bytes/save_bytes 추가)
autotable: 표 자동 레이아웃 (autofit_table)
"""
from .core import HwpxDoc, GOV_DOC_RULES
from .autotable import autofit_table

__all__ = ["HwpxDoc", "GOV_DOC_RULES", "autofit_table"]

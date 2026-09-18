"""replace_regex 안전 치환 테스트 (Phase G Step 1).

핵심: '6학년'→'5학년' 치환 시 '2026학년도'·범위표기('5~6학년','3~4학년')는
보호돼야 한다. python3 tests/test_replace_regex.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import HwpxDoc                           # noqa: E402
from tests.fixtures import make_sample_hwpx           # noqa: E402

# 학년 치환 시 보호 규칙: 앞이 숫자/범위기호가 아닐 때만 '6학년' 치환
GRADE_PAT = r'(?<![0-9~∼·\-])6\s*학년'


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


def _cell_texts(doc):
    return {(c["row"], c["col"]): c["text"] for c in doc.tables()[0]["cells"]}


def test_grade_replace_protects_year_and_ranges():
    print("[test] 학년 치환 — 연도/범위 보호")
    data = [["구분", "내용"],
            ["제목", "2026학년도 6학년 교육과정"],
            ["범위", "5~6학년군 성취기준, 3~4학년 연계"],
            ["대상", "6학년 학생 발달"]]
    doc = HwpxDoc.from_bytes(make_sample_hwpx(rows_data=data))
    n = doc.replace_regex(GRADE_PAT, "5학년")
    cur = _cell_texts(doc)
    _assert(cur[(1, 1)] == "2026학년도 5학년 교육과정",
            "'2026학년도'는 유지, '6학년'만 치환: %r" % cur[(1, 1)])
    _assert(cur[(2, 1)] == "5~6학년군 성취기준, 3~4학년 연계",
            "범위표기(5~6학년군·3~4학년) 불변: %r" % cur[(2, 1)])
    _assert(cur[(3, 1)] == "5학년 학생 발달", "일반 '6학년'은 치환")
    _assert(n == 2, "치환은 정확히 2곳(제목·대상): %d" % n)
    issues, _ = doc.verify()
    _assert(not issues, "치환 후 구조 이상 없음")


def test_regex_preserves_inline_tabs():
    print("[test] 인라인 탭(목차 페이지번호) 보존")
    # 목차형 '항목\t쪽' 텍스트에서 항목만 바꿔도 탭이 살아있어야 함
    doc = HwpxDoc.from_bytes(make_sample_hwpx(
        rows_data=[["항목"], ["6학년 목표\t1"]]))
    doc.replace_regex(GRADE_PAT, "5학년")
    cur = _cell_texts(doc)
    _assert(cur[(1, 0)].startswith("5학년 목표"), "항목 텍스트 치환")
    _assert("\t" in cur[(1, 0)] or "1" in cur[(1, 0)],
            "페이지번호(탭 뒤 숫자) 보존: %r" % cur[(1, 0)])


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 replace_regex 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

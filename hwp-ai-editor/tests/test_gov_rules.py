"""gov_rules 단위 테스트 (Phase F-2).

공문서 규정 검사기(review_document)가 날짜·시각·금액 표기와 "끝" 표시를
올바르게 검출하고, 깨끗한 문서는 오탐하지 않는지 확인한다.
python3 tests/test_gov_rules.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import HwpxDoc, review_document          # noqa: E402
from tests.fixtures import make_sample_hwpx           # noqa: E402


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


def _kinds(doc):
    return [i["kind"] for i in review_document(doc)]


def test_detects_date_time_money():
    print("[test] 날짜·시각·금액 표기 검출")
    doc = HwpxDoc.from_bytes(make_sample_hwpx([
        ["항목", "내용"],
        ["일시", "2026년 3월 1일 오후 2시"],
        ["금액", "지원금 113,560원 지급"],
    ]))
    kinds = _kinds(doc)
    _assert("날짜표기" in kinds, "'2026년 3월 1일' 날짜표기 검출")
    _assert("시각표기" in kinds, "'오후 2시' 시각표기 검출")
    _assert("금액표기" in kinds, "'113,560원' 금액표기 검출")


def test_where_is_precise():
    print("[test] 위반 위치가 표 좌표로 보고됨")
    doc = HwpxDoc.from_bytes(make_sample_hwpx([
        ["항목", "내용"],
        ["일시", "2026년 3월 1일"],
    ]))
    date_issue = next(i for i in review_document(doc) if i["kind"] == "날짜표기")
    _assert("표0" in date_issue["where"], "날짜 위반이 표0 좌표로 보고: %s"
            % date_issue["where"])


def test_no_duplicate_report():
    print("[test] 문단·셀 중복 보고 없음 (표를 감싸는 문단 제외)")
    doc = HwpxDoc.from_bytes(make_sample_hwpx([
        ["일시", "2026년 3월 1일"],
    ]))
    dates = [i for i in review_document(doc) if i["kind"] == "날짜표기"]
    _assert(len(dates) == 1, "같은 날짜가 한 번만 보고됨 (실제 %d)" % len(dates))


def test_clean_doc_no_false_positive():
    print("[test] 규정 준수 문서는 날짜·시각·금액 오탐 없음")
    doc = HwpxDoc.from_bytes(make_sample_hwpx([
        ["항목", "내용"],
        ["일시", "2026. 3. 1. 14:30"],
        ["금액", "113,560원(일십일만삼천오백육십원)"],
        ["비고", "끝."],
    ]))
    kinds = _kinds(doc)
    for k in ("날짜표기", "시각표기", "금액표기"):
        _assert(k not in kinds, "%s 오탐 없음" % k)


def test_end_marker_advisory():
    print("[test] 표로 끝나고 '끝' 없으면 권고, 있으면 없음")
    no_end = HwpxDoc.from_bytes(make_sample_hwpx([["가", "나"], ["1", "2"]]))
    _assert("끝 표시" in _kinds(no_end), "'끝' 없으면 권고")
    # '끝' 문단을 본문에 추가하면 권고 사라짐
    with_end = HwpxDoc.from_bytes(make_sample_hwpx([["가", "나"], ["1", "2"]]))
    with_end.add_paragraph("끝.")
    _assert("끝 표시" not in _kinds(with_end), "'끝' 있으면 권고 없음")


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 gov_rules 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

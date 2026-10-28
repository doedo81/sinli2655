"""표준 양식(Template) 준수 편집 검증 테스트.

pytest 없이도 실행 가능:  python3 tests/test_template.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import (HwpxDoc, extract_schema, apply_template,          # noqa: E402
                     validate_template)
from tests.fixtures import make_sample_hwpx                            # noqa: E402


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


def _blank_form():
    """헤더 1행(성명/부서/비고) + 빈 본문 1행 짜리 양식."""
    return make_sample_hwpx(rows_data=[["성명", "부서", "비고"],
                                       ["", "", ""]])


def test_extract_schema():
    print("[test] extract_schema — 고정/채움 칸 분류")
    doc = HwpxDoc.from_bytes(_blank_form())
    s = extract_schema(doc, 0)
    _assert(s["header_rows"] == [0], "헤더 행 = [0]")
    _assert(s["fill_cols"] == [0, 1, 2], "채움 열 = 0,1,2")
    _assert(s["data_rows"] == [1], "데이터 행 = [1]")
    _assert(s["repeat_row"] == 1, "반복 행 = 1")
    _assert((0, 0) in set(s["fixed"]), "헤더 (0,0)은 고정 칸")
    _assert((1, 0) in s["fillable"], "본문 (1,0)은 채움 칸")
    _assert(s["label_to_col"].get("성명") == 0, "라벨 '성명'→열 0")


def test_apply_template_grows_rows_and_keeps_header():
    print("[test] apply_template — 행 자동 증설 + 고정 칸 불변")
    doc = HwpxDoc.from_bytes(_blank_form())
    records = [["홍길동", "행정지원과", "우수"],
               ["김철수", "기획예산과 정책팀", "장기 특이사항 내용이 제법 길게 들어감"],
               ["이영희", "총무과", ""]]
    rep = apply_template(doc, 0, records)
    _assert(rep["added_rows"] == 2, "본문 1행 → 3행 (2행 증설)")

    tb = doc.tables()[0]
    cur = {(c["row"], c["col"]): c["text"] for c in tb["cells"]}
    _assert(cur[(0, 0)] == "성명" and cur[(0, 2)] == "비고",
            "헤더(고정 칸) 텍스트 불변")
    _assert(cur[(1, 0)] == "홍길동" and cur[(2, 0)] == "김철수"
            and cur[(3, 0)] == "이영희", "채움 칸 순서대로 채워짐")
    _assert(not rep["issues"], "양식/구조 문제 없음: %s" % rep["issues"])

    # autofit이 표 전체 폭을 유지하는지
    af = rep["autofit"]
    _assert(af and sum(af["widths"]) == af["total"], "표 전체 폭 유지")
    # 저장→재로딩 무결
    doc2 = HwpxDoc.from_bytes(doc.save_bytes())
    _assert(len(doc2.tables()[0]["cells"]) >= 12, "3행×3열+헤더 재로딩 정상")
    issues, _ = doc2.verify()
    _assert(not issues, "재로딩 후 verify 이상 없음")


def test_apply_template_dict_records():
    print("[test] apply_template — dict 레코드(라벨 매핑)")
    doc = HwpxDoc.from_bytes(_blank_form())
    records = [{"성명": "박보검", "비고": "메모"}]   # 부서 생략
    apply_template(doc, 0, records)
    cur = {(c["row"], c["col"]): c["text"] for c in doc.tables()[0]["cells"]}
    _assert(cur[(1, 0)] == "박보검", "라벨 '성명' 칸 채움")
    _assert(cur[(1, 2)] == "메모", "라벨 '비고' 칸 채움")
    _assert(cur[(1, 1)] == "", "생략한 '부서'는 빈 채로 유지")


def test_validate_detects_fixed_change():
    print("[test] validate_template — 고정 칸 변경 검출")
    doc = HwpxDoc.from_bytes(_blank_form())
    s = extract_schema(doc, 0)
    doc.set_cell(0, 0, 0, "이름")          # 헤더(고정 칸)를 일부러 변경
    issues = validate_template(doc, 0, s)
    _assert(any(it["kind"] == "고정칸 변경" for it in issues),
            "고정 칸 변경이 검출됨")


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 Template 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

"""엔진 회귀 + AutoTable 검증 테스트.

pytest 없이도 실행 가능:  python3 tests/test_engine.py
릴리스 기준: 편집 후 verify()가 항상 "이상 없음".
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import HwpxDoc, autofit_table          # noqa: E402
from tests.fixtures import make_sample_hwpx          # noqa: E402


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


def test_from_bytes_roundtrip():
    print("[test] from_bytes / save_bytes 왕복")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    data = doc.save_bytes()
    _assert(data[:2] == b"PK", "저장 결과가 zip(PK) 헤더")
    doc2 = HwpxDoc.from_bytes(data)
    _assert(len(doc2.tables()) == 1, "재로딩 후 표 1개")


def test_read_structure():
    print("[test] 표/문단 파싱")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    tbs = doc.tables()
    _assert(len(tbs) == 1, "표 1개 인식")
    tb = tbs[0]
    _assert(tb["rows"] == 2 and tb["cols"] == 3, "2행 3열 인식")
    cell = next(c for c in tb["cells"] if c["row"] == 0 and c["col"] == 0)
    _assert(cell["text"] == "성명", "(0,0) 셀 = '성명'")


def test_set_cell_and_verify():
    print("[test] set_cell 편집 + verify")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    doc.set_cell(0, 1, 0, "김철수")
    tb = doc.tables()[0]
    cell = next(c for c in tb["cells"] if c["row"] == 1 and c["col"] == 0)
    _assert(cell["text"] == "김철수", "셀 교체 반영")
    issues, _ = doc.verify()
    _assert(not issues, "편집 후 구조 이상 없음")


def test_autofit_widens_long_column():
    print("[test] autofit_table — 긴 내용 열만 넓어지는가")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    tb = doc.tables()[0]
    total_before = 8000 * 3
    rep = autofit_table(doc, 0)
    widths = rep["widths"]
    _assert(len(widths) == 3, "열 3개 폭 반환")
    _assert(sum(widths) == rep["total"] == total_before,
            "표 전체 폭 유지 (%d)" % sum(widths))
    # col 0 = "성명"(짧음), col 1/2 = 긴 내용 → col0 < col1, col0 < col2
    _assert(widths[0] < widths[1] and widths[0] < widths[2],
            "짧은 열(성명)이 긴 열들보다 좁음: %s" % widths)
    issues, _ = doc.verify()
    _assert(not issues, "autofit 후 구조 이상 없음")
    # 저장/재로딩까지 무결
    doc2 = HwpxDoc.from_bytes(doc.save_bytes())
    _assert(len(doc2.tables()) == 1, "autofit 결과 재로딩 정상")


def test_autofit_row_height_grows():
    print("[test] autofit_table — 넘치는 행 높이 상향")
    data = [["항목", "설명"],
            ["A", "매우 " * 40 + "긴 설명"]]   # 한 셀에 아주 긴 텍스트
    doc = HwpxDoc.from_bytes(make_sample_hwpx(rows_data=data))
    rep = autofit_table(doc, 0)
    _assert(rep["heights"], "긴 내용 행의 높이가 상향됨: %s" % rep["heights"])
    issues, _ = doc.verify()
    _assert(not issues, "구조 이상 없음")


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

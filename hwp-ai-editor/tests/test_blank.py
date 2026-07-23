"""blank 단위 테스트 (Phase F-3).

빈 HWPX 생성기가 유효한 패키지를 만들고, 엔진이 로드·편집·재저장할 수 있는지
검증한다(한/글 실제 열기는 사용자 1회 확인 게이트). 외부 파일 불필요.
python3 tests/test_blank.py
"""
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import HwpxDoc, autofit_table       # noqa: E402
from hwpxlib.blank import blank_hwpx_bytes        # noqa: E402


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


_REQUIRED = ["mimetype", "version.xml", "settings.xml",
             "META-INF/container.xml", "META-INF/manifest.xml",
             "Contents/content.hpf", "Contents/header.xml",
             "Contents/section0.xml"]


def test_package_complete():
    print("[test] 필수 8파일 + mimetype STORED·첫 항목")
    data = blank_hwpx_bytes()
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    for n in _REQUIRED:
        _assert(n in names, "%s 포함" % n)
    _assert(names[0] == "mimetype", "mimetype이 첫 항목")
    _assert(z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED,
            "mimetype 무압축(STORED)")
    _assert(z.read("mimetype") == b"application/hwp+zip", "mimetype 내용")


def test_manifest_references():
    print("[test] content.hpf·container.xml 참조 일관")
    z = zipfile.ZipFile(io.BytesIO(blank_hwpx_bytes()))
    hpf = z.read("Contents/content.hpf").decode("utf-8")
    _assert('href="Contents/header.xml"' in hpf and
            'href="Contents/section0.xml"' in hpf, "content.hpf가 header·section0 참조")
    cont = z.read("META-INF/container.xml").decode("utf-8")
    _assert('full-path="Contents/content.hpf"' in cont,
            "container.xml이 content.hpf 참조")


def test_loads_empty():
    print("[test] 엔진 로드 → 빈 문서(표0, 문단≥1, verify 이상없음)")
    doc = HwpxDoc.new()
    _assert(len(doc.tables()) == 0, "표 0개")
    _assert(len(doc.paragraphs()) >= 1, "문단 ≥ 1")
    _assert(doc.verify()[0] == [], "verify 이상 없음")


def test_roundtrip_add_table():
    print("[test] new → 표 추가 → 저장 → 재로딩 무결")
    doc = HwpxDoc.new()
    doc.add_table(2, 3, data=[["교과", "시수", "비고"], ["국어", "20", ""]])
    autofit_table(doc, 0)
    doc2 = HwpxDoc.from_bytes(doc.save_bytes())
    _assert(len(doc2.tables()) == 1, "재로딩 후 표 1개")
    _assert(doc2.verify()[0] == [], "재로딩 verify 이상 없음")
    cells = {(c["row"], c["col"]): c["text"] for c in doc2.tables()[0]["cells"]}
    _assert(cells.get((0, 0)) == "교과" and cells.get((1, 1)) == "20",
            "셀 값 유지")


def test_roundtrip_add_paragraph():
    print("[test] new → 문단 추가 → 재로딩 반영")
    doc = HwpxDoc.new()
    before = len(doc.paragraphs())
    doc.add_paragraph("2026학년도 학급 운영 계획")
    doc2 = HwpxDoc.from_bytes(doc.save_bytes())
    paras = doc2.paragraphs()
    _assert(len(paras) == before + 1, "문단 수 증가")
    _assert(any("학급 운영 계획" in t for _, _, _, t in paras), "추가 문단 반영")


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 blank 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

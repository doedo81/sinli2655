"""hwp_reader 단위 테스트 (Phase E).

레코드 파서·제어문자 처리를 합성 바이트로 검증한다(외부 파일 불필요).
python3 tests/test_hwp_reader.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib.hwp_reader import (iter_records, para_text, is_hwp,   # noqa: E402
                                HWPTAG_PARA_TEXT)


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


def _rec(tag, level, payload):
    """HWP 레코드 헤더+페이로드 조립."""
    size = len(payload)
    if size < 0xFFF:
        h = (tag & 0x3FF) | ((level & 0x3FF) << 10) | ((size & 0xFFF) << 20)
        return struct.pack("<I", h) + payload
    h = (tag & 0x3FF) | ((level & 0x3FF) << 10) | (0xFFF << 20)
    return struct.pack("<I", h) + struct.pack("<I", size) + payload


def _u16(s):
    return s.encode("utf-16-le")


def test_is_hwp():
    print("[test] OLE 시그니처 감지")
    _assert(is_hwp(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest"), ".hwp 시그니처 True")
    _assert(not is_hwp(b"PK\x03\x04rest"), ".hwpx(zip)는 False")


def test_iter_records():
    print("[test] 레코드 파싱")
    data = _rec(HWPTAG_PARA_TEXT, 0, _u16("가")) + _rec(70, 1, b"\x01\x02")
    recs = list(iter_records(data))
    _assert(len(recs) == 2, "레코드 2개")
    _assert(recs[0][0] == HWPTAG_PARA_TEXT and recs[0][1] == 0, "첫 레코드 tag/level")
    _assert(recs[1][0] == 70 and recs[1][2] == b"\x01\x02", "둘째 레코드 payload")


def test_iter_records_extended_size():
    print("[test] 확장 크기(size==0xFFF) 레코드")
    big = _u16("가" * 3000)          # 6000바이트 > 0xFFF
    data = _rec(HWPTAG_PARA_TEXT, 0, big)
    recs = list(iter_records(data))
    _assert(len(recs) == 1 and len(recs[0][2]) == len(big), "확장 크기 정확 파싱")


def test_para_text_skips_controls():
    print("[test] 제어문자 스킵 + 개행")
    # '안녕' + 확장 컨트롤(code4, 8워드=16바이트) + '끝'
    payload = _u16("안녕") + struct.pack("<H", 4) + b"\x00" * 14 + _u16("끝")
    _assert(para_text(payload) == "안녕끝", "인라인/확장 컨트롤 8워드 스킵")
    # 개행 컨트롤(13)은 줄바꿈
    p2 = _u16("가") + struct.pack("<H", 13) + _u16("나")
    _assert(para_text(p2) == "가\n나", "code13 → 개행")


def test_real_hwp_optional():
    print("[test] 실제 .hwp (있으면)")
    from hwpxlib.hwp_reader import read_hwp_text
    path = os.environ.get("HWP_SAMPLE")
    if not path or not os.path.isfile(path):
        print("  skip: HWP_SAMPLE 미지정")
        return
    r = read_hwp_text(open(path, "rb").read())
    _assert(len(r["paragraphs"]) > 0, "문단 추출 > 0")


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 hwp_reader 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

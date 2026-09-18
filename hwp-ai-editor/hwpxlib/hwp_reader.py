"""hwp_reader — 구형 .hwp(v5, OLE 복합파일) 읽기 (Phase E 1단계).

.hwp는 편집(무손실 재저장)이 어렵지만 **읽기/분석**은 표준 라이브러리(zlib/struct)
+ 작은 선택 의존성 olefile로 가능하다. 본문 텍스트를 추출해 분석·요약·규정검토의
입력으로 쓴다. (편집은 한/글에서 .hwpx로 저장 후 HwpxDoc 사용을 안내)

핵심:
- .hwp v5 = OLE 복합파일. FileHeader의 플래그로 압축 여부 판별.
- BodyText/Section* 스트림을 (압축 시) raw-deflate 해제.
- HWP 레코드 스트림 파싱 → PARA_TEXT 레코드에서 UTF-16LE 문단 텍스트 추출.
"""
import struct
import zlib

HWPTAG_BEGIN = 0x10
HWPTAG_PARA_TEXT = HWPTAG_BEGIN + 51        # 67

_OLE_SIG = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def is_hwp(data):
    """바이트열이 OLE 복합파일(.hwp v5) 시그니처인지."""
    return data[:8] == _OLE_SIG


def _require_olefile():
    try:
        import olefile
        return olefile
    except ImportError:
        raise RuntimeError(
            ".hwp 읽기에는 olefile이 필요합니다. `pip install olefile` 후 다시 시도하세요.")


def iter_records(data):
    """HWP 레코드 스트림 → (tag_id, level, payload) 제너레이터.
    레코드 헤더는 4바이트 정수: tag=하위10비트, level=다음10비트, size=상위12비트.
    size==0xFFF면 이어지는 4바이트가 실제 size."""
    i, n = 0, len(data)
    while i + 4 <= n:
        h = struct.unpack("<I", data[i:i + 4])[0]
        i += 4
        tag = h & 0x3FF
        level = (h >> 10) & 0x3FF
        size = (h >> 20) & 0xFFF
        if size == 0xFFF:
            if i + 4 > n:
                break
            size = struct.unpack("<I", data[i:i + 4])[0]
            i += 4
        yield tag, level, data[i:i + size]
        i += size


def para_text(payload):
    """PARA_TEXT 페이로드(UTF-16LE + 제어문자)에서 순수 텍스트 추출.
    제어문자(code<32): {0,10,13}=1워드(개행/무시), 그 외=확장/인라인 컨트롤 8워드(16바이트)."""
    out = []
    i, n = 0, len(payload)
    while i + 2 <= n:
        code = struct.unpack("<H", payload[i:i + 2])[0]
        if code < 32:
            if code in (10, 13):
                out.append("\n")
            i += 2 if code in (0, 10, 13) else 16
        else:
            out.append(chr(code))
            i += 2
    return "".join(out)


def read_hwp_text(source):
    """source: 바이트열 또는 파일경로. 반환:
       {"paragraphs":[...], "sections":n, "prvtext":str, "compressed":bool}"""
    olefile = _require_olefile()
    if isinstance(source, (bytes, bytearray)):
        import io
        ole = olefile.OleFileIO(io.BytesIO(bytes(source)))
    else:
        ole = olefile.OleFileIO(source)

    fh = ole.openstream("FileHeader").read()
    flags = fh[36] if len(fh) > 36 else 0
    compressed = bool(flags & 0x01)
    distributed = bool(flags & 0x04)

    prv = ""
    if ole.exists("PrvText"):
        try:
            prv = ole.openstream("PrvText").read().decode("utf-16-le", "ignore")
        except Exception:
            prv = ""

    if distributed:
        # 배포용(문서 보호) .hwp는 본문 구조가 달라 v1 미지원 → 미리보기만 제공
        ole.close()
        return {"paragraphs": [p for p in prv.split("\n") if p.strip()],
                "sections": 0, "prvtext": prv, "compressed": compressed,
                "note": "배포용(보호) .hwp라 미리보기 텍스트만 제공합니다."}

    secs = sorted("/".join(s) for s in ole.listdir()
                  if s and s[0] == "BodyText" and s[-1].startswith("Section"))
    paragraphs = []
    for s in secs:
        raw = ole.openstream(s).read()
        try:
            data = zlib.decompress(raw, -15) if compressed else raw
        except zlib.error:
            data = raw  # 압축 플래그와 실제가 다를 때 보호적으로 원본 시도
        for tag, _lv, payload in iter_records(data):
            if tag == HWPTAG_PARA_TEXT:
                t = para_text(payload).strip()
                if t:
                    paragraphs.append(t)
    ole.close()
    return {"paragraphs": paragraphs, "sections": len(secs),
            "prvtext": prv, "compressed": compressed}

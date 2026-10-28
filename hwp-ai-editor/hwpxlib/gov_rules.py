"""gov_rules — 공문서 규정 자동 검토 (결정적 검사기).

`GOV_DOC_RULES`(8개 원칙)를 프로그램적으로 점검한다. 문단·표 셀 텍스트를 훑어
날짜·시각·금액 표기, 글꼴·정렬 일관성, 표 구조, "끝" 표시를 검사하고 **보고만**
한다(자동 교정하지 않음 — 안전). 각 이슈는 근거(원칙 번호)를 함께 준다.

저수준 조회는 검증된 HwpxDoc 메서드(paragraphs/tables/check_table/verify)를
그대로 쓴다.
"""
import re

from .core import GOV_DOC_RULES  # noqa: F401  (재노출·근거 참조용)

# 원칙4 — '연월일' 대신 '2026. 3. 1.' 권장
_DATE_RE = re.compile(r"\d{4}\s*년\s*\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?")
# 원칙4 — 시각은 24시각제(14:30). '오전/오후 N시'는 권고
_TIME_RE = re.compile(r"(?:오전|오후)\s*\d{1,2}\s*시")
# 원칙5 — 금액은 '아라비아 숫자 + (한글)'. 숫자+원 뒤 괄호(한글) 없으면 권고
_MONEY_RE = re.compile(r"[\d,]{2,}\s*원(?!\s*\()")
# 원칙8 — 표 끝 처리 표시
_END_RE = re.compile(r"끝\.?|이하\s*빈\s*칸|이하\s*여백")

_PER_KIND_CAP = 30  # 종류별 이슈 상한(폭주 방지)


def _iter_text_units(doc):
    """(where, text) 쌍을 내놓는다 — 표 밖 본문 문단 + 표 셀(정확한 좌표).

    paragraphs()는 표 안 셀 문단까지 훑으므로(비탐욕 정규식이 <hp:t>를 모두
    수집), 중복 보고를 막기 위해 '표 span 안에 있는 문단'은 본문에서 제외하고
    표 셀은 tables()로 좌표까지 정확히 보고한다. 표별로 문단 span과 셀 span은
    같은 섹션에서 겹치므로 (sec, 표 span) 집합으로 판정한다."""
    tables = doc.tables()
    tspans = {}
    for tb in tables:
        tspans.setdefault(tb["sec"], []).append(tb["span"])

    def touches_table(sec, span):
        # 표를 감싸는 문단은 표보다 앞서 시작하지만 겹치므로 '겹침'으로 걸러
        # 첫 셀 텍스트의 중복 보고를 막는다.
        s, e = span
        return any(not (e <= ts or te <= s) for ts, te in tspans.get(sec, []))

    for sec, span, i, t in doc.paragraphs():
        if t and not touches_table(sec, span):
            yield ("문단 %d" % i, t)
    for tb in tables:
        for c in tb["cells"]:
            if c["text"]:
                yield ("표%d (%d,%d)" % (tb["index"], c["row"], c["col"]),
                       c["text"])


def _scan_regex(doc):
    """텍스트 표기 규정(날짜·시각·금액) 검사."""
    issues = []
    counts = {"날짜표기": 0, "시각표기": 0, "금액표기": 0}
    for where, text in _iter_text_units(doc):
        for m in _DATE_RE.finditer(text):
            if counts["날짜표기"] < _PER_KIND_CAP:
                issues.append({"kind": "날짜표기", "where": where,
                               "detail": "'%s' → '2026. 3. 1.' 형식 권장"
                                         % m.group(0).strip(),
                               "severity": "권고"})
            counts["날짜표기"] += 1
        for m in _TIME_RE.finditer(text):
            if counts["시각표기"] < _PER_KIND_CAP:
                issues.append({"kind": "시각표기", "where": where,
                               "detail": "'%s' → 24시각제 '14:30' 권장"
                                         % m.group(0).strip(),
                               "severity": "권고"})
            counts["시각표기"] += 1
        for m in _MONEY_RE.finditer(text):
            if counts["금액표기"] < _PER_KIND_CAP:
                issues.append({"kind": "금액표기", "where": where,
                               "detail": "'%s' → '113,560원(일십일만…)'처럼 한글 "
                                         "병기 권장" % m.group(0).strip(),
                               "severity": "권고"})
            counts["금액표기"] += 1
    return issues, counts


def _scan_tables(doc):
    """표별 글꼴·정렬 일관성(원칙6) + 구조 무결성 검사."""
    issues = []
    tables = doc.tables()
    for tb in tables:
        ti = tb["index"]
        rep = doc.check_table(ti)
        for key, cells in rep.get("deviations", []):
            spots = ", ".join("(%d,%d)" % (r, c) for r, c in cells[:6])
            more = " 외" if len(cells) > 6 else ""
            issues.append({
                "kind": "글꼴·정렬 일관성", "where": "표%d" % ti,
                "detail": "대표 스타일과 다른 셀 %s%s (글꼴·크기·정렬 통일 권장)"
                          % (spots, more),
                "severity": "주의"})
    struct, _ = doc.verify()
    for s in struct:
        issues.append({"kind": "표 구조", "where": "표%s" % s.get("table"),
                       "detail": s.get("detail", s.get("kind", "")),
                       "severity": "주의"})
    return issues


def _scan_end_marker(doc):
    """표가 있으면 문서 끝에 '끝'/'이하 빈칸' 표시가 있는지 확인(원칙8)."""
    if not doc.tables():
        return []
    paras = doc.paragraphs()
    tail = " ".join(t for _, _, _, t in paras[-6:] if t)
    if _END_RE.search(tail):
        return []
    return [{"kind": "끝 표시", "where": "문서 끝",
             "detail": "표로 끝나는 문서는 마지막에 '끝' 또는 '이하 빈칸' 표시 권장",
             "severity": "권고"}]


def review_document(doc):
    """공문서 규정 위반을 결정적으로 검사해 이슈 목록을 반환한다.

    반환: [{"kind","where","detail","severity"}...]. 위반이 없으면 빈 리스트.
    """
    issues, counts = _scan_regex(doc)
    issues.extend(_scan_tables(doc))
    issues.extend(_scan_end_marker(doc))
    # 상한 초과 안내
    for kind, n in counts.items():
        if n > _PER_KIND_CAP:
            issues.append({"kind": kind, "where": "(요약)",
                           "detail": "총 %d건 중 %d건만 표시" % (n, _PER_KIND_CAP),
                           "severity": "정보"})
    return issues

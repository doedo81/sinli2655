#!/usr/bin/env python3
"""
hwpx_edit.py v2 — HWPX(.hwpx) 텍스트 + 표(셀) 편집기 (외부 라이브러리 불필요)

서식 XML은 건드리지 않고 텍스트 노드만 수정한 뒤 zip을 다시 묶기 때문에
한글에서 원본 서식 그대로 열립니다. 표 안의 표(중첩 표)도 안전하게 처리합니다.

사용법:
  python3 hwpx_edit.py 파일.hwpx list
      → 문단 목록 (표 안 문단 포함)

  python3 hwpx_edit.py 파일.hwpx tables
      → 표 목록과 각 셀 내용 (행,열 좌표 포함)

  python3 hwpx_edit.py 파일.hwpx set-cell 표번호 행 열 "새 내용" -o 결과.hwpx
      → 특정 표의 특정 셀 내용 교체  (예: set-cell 0 1 2 "홍길동")

  python3 hwpx_edit.py 파일.hwpx set-cell-lines 표번호 행 열 "줄1|줄2\\t쪽|줄3" -o 결과.hwpx
      → 셀 내용을 여러 문단으로 교체 (줄마다 문단 하나, 목차용)
      → \\t는 탭(원본에 점선 리더 탭이 있으면 그 서식 재사용)
      → set-cell에서도 \\n(줄바꿈)·\\t(탭)가 한글 태그로 자동 변환됨

  python3 hwpx_edit.py 파일.hwpx replace "찾을말" "바꿀말" -o 결과.hwpx
      → 문서 전체 찾아 바꾸기 (표 안 텍스트 포함)

  python3 hwpx_edit.py 파일.hwpx add-table 행 열 --data "a|b;c|d" -o 결과.hwpx
      → 행x열 표를 새로 만들어 삽입 (--data는 세미콜론=행, 파이프=열)
      → --after 문단번호 를 주면 해당 문단 뒤에 삽입 (기본: 문서 끝)

  python3 hwpx_edit.py 파일.hwpx set-cell 표번호 행 열 "새 내용" --fit -o 결과.hwpx
      → 셀 교체 + 글자가 넘치면 크기 자동 축소 (겹침 방지)

  python3 hwpx_edit.py 파일.hwpx fit-cell 표번호 행 열 -o 결과.hwpx
      → 이미 넣은 내용에 맞춰 글자 크기 자동 조정 + 겹침 캐시 제거

  python3 hwpx_edit.py 파일.hwpx cell-font 표번호 행 열 크기pt -o 결과.hwpx
      → 셀 글자 크기를 직접 지정 (예: cell-font 2 1 3 8.5)

  python3 hwpx_edit.py 파일.hwpx verify [--fix -o 결과.hwpx]
      → 문서 전체 표 구조 검진: rowCnt/colCnt 불일치, 셀 주소 중복 등
      → --fix: 안전한 경우(주소 정상, 개수 속성만 오류)만 자동 수정
      → 편집 작업 마친 뒤 항상 verify로 마무리하는 것을 권장

  python3 hwpx_edit.py 파일.hwpx rules
      → 공문서 작성 원칙 요약 보기 (행정업무운영편람 근거)

  python3 hwpx_edit.py 파일.hwpx cell-style 표번호 행 열
      → 셀의 글꼴·크기·장평·정렬 확인 (원본 스타일 파악용)

  python3 hwpx_edit.py 파일.hwpx copy-style 표번호 행 열 참조행 참조열 -o 결과.hwpx
      → 참조 셀의 글꼴·크기·정렬을 대상 셀에 그대로 적용

  python3 hwpx_edit.py 파일.hwpx check-table 표번호(또는 all)
      → 표 안 글꼴·크기·정렬 일관성 검사, 이탈 셀 보고

  python3 hwpx_edit.py 파일.hwpx add-table 행 열 --data "..." --style-from 표번호
      → 새 표를 기존 표의 글꼴·정렬·테두리 그대로 상속해 생성

  python3 hwpx_edit.py 파일.hwpx para-info 문단번호
      → 문단의 정렬·줄간격·들여쓰기·여백 조회

  python3 hwpx_edit.py 파일.hwpx para-prop 문단번호 --spacing 123 --align 가운데
      → 문단 속성 변경 (옵션: --spacing % / --align / --indent pt
        / --left pt / --right pt / --before pt / --after pt)

  python3 hwpx_edit.py 파일.hwpx cell-prop 표번호 행 열 --spacing 123 --align 왼쪽
      → 셀 안 문단 속성 변경 (옵션 동일, 그 셀만 적용)

  python3 hwpx_edit.py 파일.hwpx del-table 표번호 -o 결과.hwpx
      → 표를 통째로 삭제 (표만 담은 문단이면 빈 줄도 안 남김)

  python3 hwpx_edit.py 파일.hwpx del-col 표번호 열 -o 결과.hwpx
      → 표에서 열을 통째로 삭제 (오른쪽 열 재번호 + 열 수 갱신 자동)
      → 가로 병합 셀이 걸치면 병합 폭을 1 줄여 안전하게 처리

  python3 hwpx_edit.py 파일.hwpx del-para 문단번호 -o 결과.hwpx
      → 최상위 문단 삭제 (표 안 문단은 거부 → set-cell로 비우세요)

  python3 hwpx_edit.py 파일.hwpx del-row 표번호 행 -o 결과.hwpx
      → 표에서 행을 통째로 삭제 (아래 행 재번호 + 행 수 갱신 자동)
      → 세로 병합 셀이 걸치면 병합 폭을 1 줄여 안전하게 처리

  python3 hwpx_edit.py 파일.hwpx clear-row 표번호 행 -o 결과.hwpx
      → 행은 남기고 그 행의 모든 셀 내용만 비움 (병합 있어도 안전)

  python3 hwpx_edit.py 파일.hwpx set-para 번호 "새 내용" -o 결과.hwpx
  python3 hwpx_edit.py 파일.hwpx add-para "추가할 문단" -o 결과.hwpx
"""
import io
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape

# ----------------------------------------------------------------
# 공통 유틸
# ----------------------------------------------------------------
def _detect_prefix(xml_text, local):
    m = re.search(r"<(\w+):%s[\s>/]" % local, xml_text)
    return m.group(1) if m else "hp"

def _t_pattern(prefix):
    return re.compile(
        r"(<%(p)s:t(?:\s[^>]*)?>)(.*?)(</%(p)s:t>)" % {"p": prefix}, re.DOTALL)

def _t_selfclose_pattern(prefix):
    return re.compile(r"<%s:t(\s[^>]*)?/>" % prefix)

def _p_pattern(prefix):
    return re.compile(r"<%(p)s:p[\s>].*?</%(p)s:p>" % {"p": prefix}, re.DOTALL)

def _unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&apos;", "'")
             .replace("&amp;", "&"))

def _rich_text(prefix, s, tab_tag=None):
    """새 텍스트의 \t/\n을 한글이 인식하는 태그로 변환.
    tab_tag가 주어지면(원본 셀의 점선 리더 탭 등) 그 형태를 재사용."""
    s = escape(s)
    s = s.replace("\t", tab_tag or ("<%s:tab/>" % prefix))
    s = s.replace("\n", "<%s:lineBreak/>" % prefix)
    return s

def _clean_inline(s):
    """<hp:t> 사이에 낀 tab/lineBreak 등 인라인 태그를 보기 좋게 정리.
    (표시/추출용. 실제 저장 XML은 건드리지 않음)"""
    s = re.sub(r"<\w+:tab\b[^>]*/?>", "\t", s)
    s = re.sub(r"<\w+:lineBreak\b[^>]*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)   # 남은 인라인 태그 제거
    return s

def _find_elements(xml, qname):
    """<qname ...> ... </qname> 완전한 요소들의 (시작,끝) 목록.
    같은 태그가 중첩돼도(표 안의 표) 각각 올바른 짝을 찾는다."""
    spans = []
    tag_re = re.compile(r"<(/?)%s(?=[\s/>])" % re.escape(qname))
    stack = []
    for m in tag_re.finditer(xml):
        gt = xml.find(">", m.end())
        if gt < 0:
            break
        if m.group(1) == "/":          # 닫는 태그
            if stack:
                spans.append((stack.pop(), gt + 1))
        elif xml[gt - 1] == "/":       # 자기닫힘 태그
            spans.append((m.start(), gt + 1))
        else:                          # 여는 태그
            stack.append(m.start())
    return sorted(spans)

def _first_outside(pattern, text, nested):
    """중첩 영역(nested) 밖에 있는 첫 정규식 매치 반환."""
    for m in pattern.finditer(text):
        if not _inside_any((m.start(), m.end()), nested):
            return m
    return None

def _inside_any(pos_span, regions):
    s, e = pos_span
    return any(rs < s and e <= re_ for rs, re_ in regions)

def _first_attr(xml, tag, attr):
    """<...tag ... attr="값" ...> 에서 첫 attr 값을 찾아 반환 (없으면 None)"""
    for m in re.finditer(r"<%s\b[^>]*>" % re.escape(tag), xml):
        a = re.search(r'\b%s="([^"]*)"' % re.escape(attr), m.group(0))
        if a:
            return a.group(1)
    return None

# ----------------------------------------------------------------
# HWPX 문서
# ----------------------------------------------------------------
# ----------------------------------------------------------------
# 공문서 작성 원칙 (행정업무의 운영 및 혁신에 관한 규정 시행규칙 제2조,
# 행정안전부 행정업무운영편람 근거 요약)
# ----------------------------------------------------------------
GOV_DOC_RULES = """\
[공문서 작성 원칙 요약 — 편집 시 참조]
1. 항목 기호 순서: 1. → 가. → 1) → 가) → (1) → (가) → ① → ㉮
   (필요시 □, ○, -, · 특수기호 허용)
2. 들여쓰기: 첫째 항목은 왼쪽 기본선에서 시작,
   둘째 항목부터 상위 항목 위치에서 오른쪽으로 2타씩.
   항목 기호와 내용 사이는 1타. 항목이 하나뿐이면 기호 생략.
3. 두 줄 이상 항목은 둘째 줄부터 첫 글자에 맞춰 정렬(문서 내 통일).
4. 날짜: 2026. 3. 1. (연월일 대신 마침표+1타), 시각: 14:30 (24시각제)
5. 금액: 아라비아 숫자 + 괄호 한글 (예: 113,560원(일십일만삼천오백육십원))
6. 글꼴: 규정상 지정 없음. 단 하나의 문서/표 안에서는 글꼴·크기 통일.
7. 줄 간격 기본 123%. 표 안 글자가 윗선에 붙어 보이면 줄 간격 확인.
8. 표가 마지막 칸까지 차면 표 아래 왼쪽 기본선에서 2타 띄우고 "끝" 표시,
   중간에서 끝나면 다음 줄에 "이하 빈칸" 표시.
"""

_ALIGN_KO = {"LEFT": "왼쪽", "CENTER": "가운데", "RIGHT": "오른쪽",
             "JUSTIFY": "양쪽", "DISTRIBUTE": "배분", "BOTH": "양쪽"}
_ALIGN_EN = {"왼쪽": "LEFT", "가운데": "CENTER", "중앙": "CENTER",
             "오른쪽": "RIGHT", "양쪽": "JUSTIFY", "배분": "DISTRIBUTE"}

class HwpxDoc:
    def __init__(self, path):
        self.path = path
        with zipfile.ZipFile(path) as zf:
            self.names = zf.namelist()
            self.files = {n: zf.read(n) for n in self.names}
        self.sections = sorted(n for n in self.names
                               if re.fullmatch(r"Contents/section\d+\.xml", n))
        if not self.sections:
            raise ValueError("Contents/section*.xml이 없습니다. HWPX 파일이 맞나요?")

    @classmethod
    def from_bytes(cls, data, name="<memory>"):
        """바이트열(업로드된 HWPX)에서 직접 로드 — 웹 서버용.
        파일 경로 없이 메모리에서 열고 편집할 수 있게 한다."""
        self = cls.__new__(cls)
        self.path = name
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            self.names = zf.namelist()
            self.files = {n: zf.read(n) for n in self.names}
        self.sections = sorted(n for n in self.names
                               if re.fullmatch(r"Contents/section\d+\.xml", n))
        if not self.sections:
            raise ValueError("Contents/section*.xml이 없습니다. HWPX 파일이 맞나요?")
        return self

    @classmethod
    def new(cls):
        """빈 HWPX 문서를 새로 만든다(문서 없이 생성 시작).
        hwpxlib/assets/blank.hwpx(사용자 제공 씨앗)가 있으면 우선 사용하고,
        없으면 합성 뼈대(blank.blank_hwpx_bytes)를 쓴다. 이후 add_table 등으로 채운다."""
        from .blank import blank_hwpx_bytes, seed_path
        sp = seed_path()
        if os.path.isfile(sp):
            with open(sp, "rb") as f:
                return cls.from_bytes(f.read(), name="<new>")
        return cls.from_bytes(blank_hwpx_bytes(), name="<new>")

    def save_bytes(self):
        """편집 결과를 HWPX 바이트열로 반환 — 웹 다운로드용.
        mimetype은 규격대로 무압축(STORED)으로 먼저 기록한다."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            if "mimetype" in self.files:
                zf.writestr(zipfile.ZipInfo("mimetype"), self.files["mimetype"],
                            compress_type=zipfile.ZIP_STORED)
            for n in self.names:
                if n != "mimetype":
                    zf.writestr(n, self.files[n])
        return buf.getvalue()

    def save(self, out_path):
        with open(out_path, "wb") as f:
            f.write(self.save_bytes())

    # ---------- 문단 ----------
    def paragraphs(self):
        out, idx = [], 0
        for sec in self.sections:
            xml = self.files[sec].decode("utf-8")
            p = _detect_prefix(xml, "p")
            tp = _t_pattern(_detect_prefix(xml, "t"))
            for m in _p_pattern(p).finditer(xml):
                text = _clean_inline(_unescape("".join(t.group(2)
                                         for t in tp.finditer(m.group(0)))))
                out.append((sec, m.span(), idx, text))
                idx += 1
        return out

    # ---------- 표 ----------
    def tables(self):
        """[{'sec', 'span', 'index', 'rows', 'cols', 'cells':
             [{'row','col','span','text'}...], 'nested': n개}] 반환"""
        result, tidx = [], 0
        for sec in self.sections:
            xml = self.files[sec].decode("utf-8")
            hp = _detect_prefix(xml, "tbl") if "<" in xml else "hp"
            hp = _detect_prefix(xml, "tbl")
            tbl_spans = _find_elements(xml, "%s:tbl" % hp)
            for ts in tbl_spans:
                nested = [o for o in tbl_spans if o != ts and _inside_any(o, [ts])]
                cells = self._parse_cells(xml, ts, nested, hp)
                rows = 1 + max((c["row"] for c in cells), default=-1)
                cols = 1 + max((c["col"] for c in cells), default=-1)
                result.append({"sec": sec, "span": ts, "index": tidx,
                               "rows": rows, "cols": cols,
                               "cells": cells, "nested": len(nested)})
                tidx += 1
        return result

    def _parse_cells(self, xml, tbl_span, nested, hp):
        s, e = tbl_span
        body = xml
        tc_spans = [c for c in _find_elements(body, "%s:tc" % hp)
                    if s < c[0] and c[1] <= e and not _inside_any(c, nested)]
        tp = _t_pattern(_detect_prefix(xml, "t"))
        addr_re = re.compile(
            r'<%s:cellAddr[^>]*colAddr="(\d+)"[^>]*rowAddr="(\d+)"' % hp)
        addr_re2 = re.compile(
            r'<%s:cellAddr[^>]*rowAddr="(\d+)"[^>]*colAddr="(\d+)"' % hp)
        cells = []
        for order, cs in enumerate(tc_spans):
            chunk = body[cs[0]:cs[1]]
            base = cs[0]
            # 셀 자신의 좌표 — 중첩 표 내부의 cellAddr는 제외하고 찾기
            cell_nested = [(ns - base, ne - base) for ns, ne in nested
                           if base < ns and ne <= cs[1]]
            row = col = None
            m = _first_outside(addr_re, chunk, cell_nested)
            if m:
                col, row = int(m.group(1)), int(m.group(2))
            else:
                m = _first_outside(addr_re2, chunk, cell_nested)
                if m:
                    row, col = int(m.group(1)), int(m.group(2))
            if row is None:
                row, col = 0, order
            # 셀 텍스트 (중첩 표 내부 제외, 문단 사이는 줄바꿈으로)
            hp2 = _detect_prefix(body, "p")
            p_local = [(base + ps, base + pe) for ps, pe in
                       _find_elements(chunk, "%s:p" % hp2)]
            p_local = [p for p in p_local if not _inside_any(p, nested)]
            p_local = [p for p in p_local
                       if not any(q[0] < p[0] and p[1] <= q[1]
                                  for q in p_local if q != p)]
            para_texts = []
            if p_local:
                for ps, pe in p_local:
                    ts = [t.group(2) for t in
                          tp.finditer(body[ps:pe])
                          if not _inside_any((ps + t.start(), ps + t.end()),
                                             nested)]
                    para_texts.append("".join(ts))
                joined = "\n".join(para_texts)
            else:
                ts = []
                for t in tp.finditer(chunk):
                    abs_span = (base + t.start(), base + t.end())
                    if not _inside_any(abs_span, nested):
                        ts.append(t.group(2))
                joined = "".join(ts)
            cells.append({"row": row, "col": col, "span": cs,
                          "text": _clean_inline(_unescape(joined))})
        return cells

    def set_cell(self, table_index, row, col, new_text):
        tables = self.tables()
        if not (0 <= table_index < len(tables)):
            raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
        tb = tables[table_index]
        target = next((c for c in tb["cells"]
                       if c["row"] == row and c["col"] == col), None)
        if target is None:
            raise IndexError("표 %d에 (행 %d, 열 %d) 셀이 없습니다. "
                             "(병합된 셀일 수 있음)" % (table_index, row, col))
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        # 최신 좌표 기준으로 다시 계산된 span 사용
        cs, ce = target["span"]
        chunk = xml[cs:ce]
        nested_local = [(ns - cs, ne - cs) for ns, ne in
                        _find_elements(chunk, "%s:tbl" % hp)]
        tprefix = _detect_prefix(xml, "t")
        # 셀에 이미 있는 탭 태그(점선 리더 등)를 재사용해 서식 유지
        tab_m = re.search(r"<%s:tab\b[^>]*/>" % tprefix, chunk)
        tab_tag = tab_m.group(0) if tab_m else None
        tpat = _t_pattern(tprefix)
        matches = [m for m in tpat.finditer(chunk)
                   if not _inside_any((m.start(), m.end()), nested_local)]
        if matches:
            pieces, pos = [], 0
            for i, m in enumerate(matches):
                pieces.append(chunk[pos:m.start()])
                body = _rich_text(tprefix, new_text, tab_tag) if i == 0 else ""
                pieces.append(m.group(1) + body + m.group(3))
                pos = m.end()
            pieces.append(chunk[pos:])
            new_chunk = "".join(pieces)
        else:
            scpat = _t_selfclose_pattern(tprefix)
            sm = next((m for m in scpat.finditer(chunk)
                       if not _inside_any((m.start(), m.end()), nested_local)),
                      None)
            if sm is not None:
                attrs = sm.group(1) or ""
                new_chunk = (chunk[:sm.start()]
                             + "<%s:t%s>%s</%s:t>" % (tprefix, attrs,
                                                      _rich_text(tprefix, new_text, tab_tag),
                                                      tprefix)
                             + chunk[sm.end():])
            else:
                # <hp:t>가 전혀 없는 완전 빈 셀:
                # run 태그 안에 새 t 노드를 삽입 (서식 charPrIDRef 유지)
                rprefix = _detect_prefix(xml, "run")
                # 1) 자기닫힘 run: <hp:run .../>  →  <hp:run ...><hp:t>내용</hp:t></hp:run>
                run_sc = re.compile(r"<%s:run\b([^>]*?)/>" % rprefix)
                rm = next((m for m in run_sc.finditer(chunk)
                           if not _inside_any((m.start(), m.end()), nested_local)),
                          None)
                if rm is not None:
                    attrs = rm.group(1)
                    repl = ("<%s:run%s><%s:t>%s</%s:t></%s:run>"
                            % (rprefix, attrs, tprefix,
                               _rich_text(tprefix, new_text, tab_tag),
                               tprefix, rprefix))
                    new_chunk = chunk[:rm.start()] + repl + chunk[rm.end():]
                else:
                    # 2) 여는 run 태그가 있으면 그 직후에 t 삽입
                    run_open = re.compile(r"<%s:run\b[^>]*>" % rprefix)
                    rm = next((m for m in run_open.finditer(chunk)
                               if not _inside_any((m.start(), m.end()),
                                                  nested_local)), None)
                    if rm is None:
                        raise ValueError("이 셀에서 텍스트를 넣을 위치를 찾지 못했습니다.")
                    ins = rm.end()
                    new_chunk = (chunk[:ins]
                                 + "<%s:t>%s</%s:t>" % (tprefix,
                                                        _rich_text(tprefix, new_text, tab_tag),
                                                        tprefix)
                                 + chunk[ins:])
        # lineseg(줄배치 캐시)는 유지한다 — 제거하면 한글이 렌더링을 멈춘다!
        self.files[sec] = (xml[:cs] + new_chunk + xml[ce:]).encode("utf-8")

    def set_cell_paras(self, table_index, row, col, lines,
                        tab_model=None, ratio=1.6509):
        """셀 내용을 여러 줄로 교체 (스타일 자동 매칭판).
        - 줄 종류 자동 감지: 로마숫자 시작=장제목, ''=빈 줄, 그 외=항목
        - 셀 안 기존 문단에서 장제목/항목/빈줄 템플릿을 찾아 복제
          (lineseg 보존 → 한글 렌더링 안전)
        - vertpos는 이전 문단 vertsize×ratio(1.6509)씩 누적
        - 항목의 '텍스트\t번호'는 탭 width를 tab_model
          {'C','H','A'} (width = C - H×전각 - A×반각)로 재계산해
          페이지 번호 끝을 정렬한다."""
        tb, target = self._cell_chunk(table_index, row, col)
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        cs, ce = target["span"]
        chunk = xml[cs:ce]
        spans = _find_elements(chunk, "%s:tbl" % hp)
        outer = max(spans, key=lambda sp: sp[1] - sp[0]) if spans else None
        nested_local = [sp for sp in spans if sp != outer] if outer else spans
        tprefix = _detect_prefix(xml, "t")

        p_spans = [p for p in _find_elements(chunk, "%s:p" % hp)
                   if not _inside_any(p, nested_local)]
        p_spans = [p for p in p_spans
                   if not any(q[0] < p[0] and p[1] <= q[1]
                              for q in p_spans if q != p)]
        if not p_spans:
            raise ValueError("이 셀에서 문단을 찾지 못했습니다.")
        p_spans.sort()
        bodies = [chunk[s:e] for s, e in p_spans]

        def vsize(b):
            mm = re.search(r'vertsize="(\d+)"', b)
            return int(mm.group(1)) if mm else 1100

        def text_of(b):
            return "".join(re.findall(r'<%s:t[^>]*>([^<]*)' % tprefix, b))

        heading_tpl = next((b for b in bodies if vsize(b) >= 1200), None)
        item_tpl = next((b for b in bodies
                         if ("<%s:tab" % tprefix) in b), None)
        blank_tpl = next((b for b in bodies if not text_of(b).strip()),
                         None)
        base_tpl = item_tpl or bodies[0]
        if heading_tpl is None:
            heading_tpl = base_tpl
        if blank_tpl is None:
            blank_tpl = base_tpl

        def char_counts(s):
            h = sum(1 for ch in s if ord(ch) > 0x1100)
            return h, len(s) - h

        def set_vertpos(b, v):
            return re.sub(r'vertpos="\d+"', 'vertpos="%d"' % v, b)

        def fill_text(b, content_xml):
            # 첫 t에 content, 나머지 t 비움 (탭 등 내부 태그는 content에 포함)
            tpat = _t_pattern(tprefix)
            ms = list(tpat.finditer(b))
            if not ms:
                return b
            pieces, pos = [], 0
            for i, mm in enumerate(ms):
                pieces.append(b[pos:mm.start()])
                pieces.append("<%s:t>%s</%s:t>"
                              % (tprefix, content_xml if i == 0 else "",
                                 tprefix)
                              if i == 0 or mm.group(2)
                              else mm.group(0))
                pos = mm.end()
            pieces.append(b[pos:])
            return "".join(pieces)

        roman = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"
        new_paras = []
        v = None
        for line in lines:
            if line == "":
                tpl, kind = blank_tpl, "blank"
            elif line.lstrip()[:1] in roman:
                tpl, kind = heading_tpl, "heading"
            else:
                tpl, kind = item_tpl or base_tpl, "item"
            if v is None:
                mm = re.search(r'vertpos="(\d+)"', tpl)
                v = int(mm.group(1)) if mm else 0
                v = 0
            body = set_vertpos(tpl, v)
            if kind == "item" and "\t" in line and tab_model \
                    and ("<%s:tab" % tprefix) in body:
                left, num = line.rsplit("\t", 1)
                full = left + num
                if "charw" in tab_model:
                    cw = tab_model["charw"]
                    half = tab_model.get("HALF", 550.0)
                    dh = tab_model.get("default_h", 1069.0)
                    tw = sum(cw.get(ch, dh) if ord(ch) > 0x2E80
                             else half for ch in full)
                    w = int(round(tab_model["C"] - tw))
                else:
                    h1, a1 = char_counts(left)
                    h2, a2 = char_counts(num)
                    w = int(round(tab_model["C"]
                                  - tab_model["H"] * (h1 + h2)
                                  - tab_model["A"] * (a1 + a2)))
                w = max(w, 300)
                tabm = re.search(r"<%s:tab\b[^>]*/>" % tprefix, body)
                tab_tag = re.sub(r'width="\d+"', 'width="%d"' % w,
                                 tabm.group(0))
                content = escape(left) + tab_tag + escape(num)
            else:
                content = _rich_text(tprefix, line, None)
            body = fill_text(body, content)
            new_paras.append(body)
            v += int(round(vsize(tpl) * ratio))

        head = chunk[:p_spans[0][0]]
        tail = chunk[p_spans[-1][1]:]
        new_chunk = head + "".join(new_paras) + tail
        self.files[sec] = (xml[:cs] + new_chunk + xml[ce:]).encode("utf-8")
        return len(lines)


    def _next_id(self, xml):
        ids = [int(x) for x in re.findall(r'\bid="(\d+)"', xml)]
        return (max(ids) + 1) if ids else 1000

    def _reuse_border_fill(self, xml):
        """문서에 이미 쓰인 표/셀의 borderFillIDRef를 재사용.
        없으면 header.xml의 borderFill 개수로 유효 ID를 고른다."""
        b = _first_attr(xml, "hp:tc", "borderFillIDRef")
        if b:
            return b
        b = _first_attr(xml, "hp:tbl", "borderFillIDRef")
        if b:
            return b
        # header.xml에서 borderFill 정의를 찾아 마지막 것을 사용
        for name in self.names:
            if name.endswith("header.xml"):
                htext = self.files[name].decode("utf-8", "ignore")
                bids = re.findall(r'<hh:borderFill\b[^>]*\bid="(\d+)"', htext)
                bids += re.findall(r'<hp:borderFill\b[^>]*\bid="(\d+)"', htext)
                if bids:
                    return bids[-1]
        return "1"  # 최후의 기본값

    def add_table(self, rows, cols, data=None, char_pr="0", para_pr="0",
                  col_width=8000, row_height=2000, after_paragraph=None,
                  border_fill=None):
        """rows x cols 표를 만들어 문서 끝(또는 지정 문단 뒤)에 삽입.
        data: 2차원 리스트(행×열)의 셀 텍스트. 부족하면 빈 셀."""
        sec = self.sections[-1]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "p")
        bf = border_fill or self._reuse_border_fill(xml)
        nid = self._next_id(xml)

        def esc(v):
            return escape("" if v is None else str(v))

        tbl_id = nid
        pid = nid + 1
        trs = []
        for r in range(rows):
            tcs = []
            for c in range(cols):
                val = ""
                if data and r < len(data) and c < len(data[r]):
                    val = data[r][c]
                tcs.append(
                    '<%(hp)s:tc borderFillIDRef="%(bf)s">'
                    '<%(hp)s:cellAddr colAddr="%(c)d" rowAddr="%(r)d"/>'
                    '<%(hp)s:cellSpan colSpan="1" rowSpan="1"/>'
                    '<%(hp)s:cellSz width="%(w)d" height="%(h)d"/>'
                    '<%(hp)s:subList>'
                    '<%(hp)s:p paraPrIDRef="%(ppr)s" styleIDRef="0">'
                    '<%(hp)s:run charPrIDRef="%(cpr)s">'
                    '<%(hp)s:t>%(v)s</%(hp)s:t></%(hp)s:run></%(hp)s:p>'
                    '</%(hp)s:subList></%(hp)s:tc>'
                    % {"hp": hp, "bf": bf, "c": c, "r": r,
                       "w": col_width, "h": row_height,
                       "ppr": para_pr, "cpr": char_pr, "v": esc(val)})
            trs.append("<%s:tr>%s</%s:tr>" % (hp, "".join(tcs), hp))

        table_xml = (
            '<%(hp)s:p paraPrIDRef="%(ppr)s" styleIDRef="0" id="%(pid)d">'
            '<%(hp)s:run charPrIDRef="%(cpr)s">'
            '<%(hp)s:tbl id="%(tid)d" rowCnt="%(R)d" colCnt="%(C)d" '
            'borderFillIDRef="%(bf)s" pageBreak="CELL" repeatHeader="0">'
            '<%(hp)s:sz width="%(tw)d" height="%(th)d"/>'
            '%(rows)s'
            '</%(hp)s:tbl></%(hp)s:run></%(hp)s:p>'
            % {"hp": hp, "ppr": para_pr, "cpr": char_pr,
               "pid": pid, "tid": tbl_id, "R": rows, "C": cols, "bf": bf,
               "tw": col_width * cols, "th": row_height * rows,
               "rows": "".join(trs)})

        # 삽입 위치 결정
        if after_paragraph is not None:
            paras = self.paragraphs()
            if not (0 <= after_paragraph < len(paras)):
                raise IndexError("문단 번호 범위를 벗어났습니다.")
            psec, (ps, pe), _, _ = paras[after_paragraph]
            if psec != sec:
                sec = psec
                xml = self.files[sec].decode("utf-8")
            insert_at = pe
        else:
            # 섹션 닫는 태그 바로 앞
            m = re.search(r"</\w+:sec>\s*$", xml)
            insert_at = m.start() if m else len(xml)

        self.files[sec] = (xml[:insert_at] + table_xml + xml[insert_at:]).encode("utf-8")
        return {"table_id": tbl_id, "rows": rows, "cols": cols, "border_fill": bf}

    # ---------- 행/열 삭제 (병합 인식) ----------
    def _del_line(self, table_index, idx, axis):
        """axis='row' 또는 'col'. 병합 셀은 폭을 1 줄여서 처리(한글과 동일한 방식).
        - 해당 줄에서 span=1인 셀은 제거
        - 해당 줄에 걸친 병합 셀은 colSpan/rowSpan을 1 감소 (내용 보존)
        - 뒤 줄들의 좌표 재번호, rowCnt/colCnt와 표 크기 갱신"""
        tables = self.tables()
        if not (0 <= table_index < len(tables)):
            raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
        tb = tables[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        s, e = tb["span"]
        chunk = xml[s:e]

        addr_attr = "rowAddr" if axis == "row" else "colAddr"
        span_attr = "rowSpan" if axis == "row" else "colSpan"
        size_attr = "height" if axis == "row" else "width"
        cnt_attr = "rowCnt" if axis == "row" else "colCnt"

        def local_nested(c):
            spans = _find_elements(c, "%s:tbl" % hp)
            outer = max(spans, key=lambda sp: sp[1] - sp[0]) if spans else None
            return [sp for sp in spans if sp != outer]

        nested = local_nested(chunk)
        tc_spans = [c for c in _find_elements(chunk, "%s:tc" % hp)
                    if not _inside_any(c, nested)]

        def cell_nested_of(cs_, ce_):
            return [(ns - cs_, ne - cs_) for ns, ne in nested
                    if cs_ < ns and ne <= ce_]

        def first_attr_m(cell, cn, tag, attr):
            pat = re.compile(r'(<%s:%s\b[^>]*\b%s=")(\d+)(")'
                             % (hp, tag, attr))
            return _first_outside(pat, cell, cn)

        # 셀 메타 수집 (중첩 표 내부의 주소는 제외)
        info = []
        for cs_, ce_ in tc_spans:
            cell = chunk[cs_:ce_]
            cn = cell_nested_of(cs_, ce_)
            am = first_attr_m(cell, cn, "cellAddr", addr_attr)
            if am is None:
                continue
            a0 = int(am.group(2))
            sm = first_attr_m(cell, cn, "cellSpan", span_attr)
            sp = int(sm.group(2)) if sm else 1
            zm = first_attr_m(cell, cn, "cellSz", size_attr)
            sz = int(zm.group(2)) if zm else None
            info.append((cs_, ce_, a0, sp, sz))

        if not any(a0 <= idx < a0 + sp for _, _, a0, sp, _ in info):
            raise IndexError("표 %d에서 %s %d을 찾지 못했습니다."
                             % (table_index, "행" if axis == "row" else "열", idx))

        # 삭제되는 줄의 크기(재계산용): span=1 셀의 height/width
        line_size = next((sz for _, _, a0, sp, sz in info
                          if a0 == idx and sp == 1 and sz), None)

        # 뒤에서부터 셀별 처리 (오프셋 보존)
        def sub_at(cell, m, val):
            return cell[:m.start(2)] + str(val) + cell[m.end(2):]

        for cs_, ce_, a0, sp, sz in sorted(info, reverse=True):
            cell = chunk[cs_:ce_]
            if a0 == idx and sp == 1:
                chunk = chunk[:cs_] + chunk[ce_:]      # 셀 제거
                continue
            cn = cell_nested_of(cs_, ce_)
            new_cell = cell
            if a0 <= idx < a0 + sp and sp > 1:
                # 병합 폭 1 감소 (내용 보존)
                m = first_attr_m(new_cell, cn, "cellSpan", span_attr)
                if m:
                    new_cell = sub_at(new_cell, m, sp - 1)
                if line_size and sz:
                    m = first_attr_m(new_cell, cn, "cellSz", size_attr)
                    if m:
                        new_cell = sub_at(new_cell, m,
                                          max(sz - line_size, 1))
            if a0 > idx:
                m = first_attr_m(new_cell, cn, "cellAddr", addr_attr)
                if m:
                    new_cell = sub_at(new_cell, m, a0 - 1)
            if new_cell != cell:
                chunk = chunk[:cs_] + new_cell + chunk[ce_:]

        # 행 삭제면: 셀이 전부 빠져 빈 <hp:tr></hp:tr>이 된 행 제거
        if axis == "row":
            chunk = re.sub(r"<%s:tr\b[^>]*>\s*</%s:tr>" % (hp, hp), "", chunk)
            # 삭제된 행에서 '시작'하던 병합 셀만 남은 tr은
            # 다음 tr(같은 rowAddr가 된)과 합쳐 행 수를 맞춘다
            nested3 = local_nested(chunk)
            tr_spans = [t for t in _find_elements(chunk, "%s:tr" % hp)
                        if not _inside_any(t, nested3)]

            def tr_first_row(tspan):
                m = re.search(r'rowAddr="(\d+)"', chunk[tspan[0]:tspan[1]])
                return int(m.group(1)) if m else None

            for i in range(len(tr_spans) - 1):
                r1 = tr_first_row(tr_spans[i])
                r2 = tr_first_row(tr_spans[i + 1])
                if r1 is not None and r1 == r2:
                    s1, e1 = tr_spans[i]
                    s2, e2 = tr_spans[i + 1]
                    tr1 = chunk[s1:e1]
                    tr2 = chunk[s2:e2]
                    om1 = re.match(r"<%s:tr\b[^>]*>" % hp, tr1)
                    om2 = re.match(r"<%s:tr\b[^>]*>" % hp, tr2)
                    close_len = len("</%s:tr>" % hp)
                    inner1 = tr1[om1.end():-close_len]
                    new_tr2 = tr2[:om2.end()] + inner1 + tr2[om2.end():]
                    chunk = (chunk[:s1] + chunk[e1:s2]
                             + new_tr2 + chunk[e2:])
                    break

        # rowCnt/colCnt 갱신 — 빼기 연산 대신 실제 구조에서 재계산
        # (연쇄 편집 후에도 불일치가 생기지 않도록)
        chunk = self._resync_counts_chunk(chunk, hp)

        # 표 전체 크기 갱신 (표 자신의 첫 <hp:sz>)
        if line_size:
            chunk = re.sub(
                r'(<%s:sz\b[^>]*\b%s=")(\d+)(")' % (hp, size_attr),
                lambda m: m.group(1)
                + str(max(int(m.group(2)) - line_size, 1)) + m.group(3),
                chunk, count=1)

        self.files[sec] = (xml[:s] + chunk + xml[e:]).encode("utf-8")

    def _tbl_actual_counts(self, chunk, hp):
        """표 chunk의 실제 (행 수, 열 수, 주소기반 행 수, 주소중복목록)"""
        spans = _find_elements(chunk, "%s:tbl" % hp)
        outer = max(spans, key=lambda sp: sp[1] - sp[0]) if spans else None
        nested = [sp for sp in spans if sp != outer] if outer else spans
        tr_spans = [t for t in _find_elements(chunk, "%s:tr" % hp)
                    if not _inside_any(t, nested)]
        tc_spans = [c for c in _find_elements(chunk, "%s:tc" % hp)
                    if not _inside_any(c, nested)]
        addr_re = re.compile(
            r'<%s:cellAddr[^>]*colAddr="(\d+)"[^>]*rowAddr="(\d+)"' % hp)
        span_re = re.compile(
            r'<%s:cellSpan[^>]*colSpan="(\d+)"[^>]*rowSpan="(\d+)"' % hp)
        max_r = max_c = 0
        seen, dups = set(), []
        for cs_, ce_ in tc_spans:
            cell = chunk[cs_:ce_]
            cell_nested = [(ns - cs_, ne - cs_) for ns, ne in nested
                           if cs_ < ns and ne <= ce_]
            am = _first_outside(addr_re, cell, cell_nested)
            if not am:
                continue
            c0, r0 = int(am.group(1)), int(am.group(2))
            sm = _first_outside(span_re, cell, cell_nested)
            cs2 = int(sm.group(1)) if sm else 1
            rs2 = int(sm.group(2)) if sm else 1
            max_r = max(max_r, r0 + rs2)
            max_c = max(max_c, c0 + cs2)
            if (r0, c0) in seen:
                dups.append((r0, c0))
            seen.add((r0, c0))
        return len(tr_spans), max_c, max_r, dups

    def _resync_counts_chunk(self, chunk, hp):
        """표 여는 태그의 rowCnt/colCnt를 실제 구조로 재계산해 기록."""
        rows, cols, _, _ = self._tbl_actual_counts(chunk, hp)
        open_tag = re.match(r"<%s:tbl\b[^>]*>" % hp, chunk)
        if not open_tag or rows == 0:
            return chunk
        new_open = re.sub(r'(\browCnt=")(\d+)(")',
                          lambda m: m.group(1) + str(rows) + m.group(3),
                          open_tag.group(0), count=1)
        new_open = re.sub(r'(\bcolCnt=")(\d+)(")',
                          lambda m: m.group(1) + str(max(cols, 1)) + m.group(3),
                          new_open, count=1)
        return new_open + chunk[open_tag.end():]

    def verify(self, fix=False):
        """문서 전체 표 구조 검진.
        - rowCnt/colCnt 속성 vs 실제 행·열 수 불일치 (fix=True면 자동 수정)
        - 셀 주소 중복, 주소기반 행수와 실제 행수 불일치는 보고만
        반환: 문제 목록 [{table, kind, detail}]"""
        issues = []
        fix_targets = {}          # sec → [(span, hp)]
        tables = self.tables()    # 한 번만 파싱
        for i, tb in enumerate(tables):
            sec = tb["sec"]
            xml = self.files[sec].decode("utf-8")
            hp = _detect_prefix(xml, "tbl")
            s, e = tb["span"]
            chunk = xml[s:e]
            rows, cols, addr_rows, dups = self._tbl_actual_counts(chunk, hp)
            om = re.match(r"<%s:tbl\b[^>]*>" % hp, chunk)
            rm = re.search(r'\browCnt="(\d+)"', om.group(0)) if om else None
            cm = re.search(r'\bcolCnt="(\d+)"', om.group(0)) if om else None
            attr_r = int(rm.group(1)) if rm else None
            attr_c = int(cm.group(1)) if cm else None
            bad = False
            if attr_r is not None and rows and attr_r != rows:
                issues.append({"table": i, "kind": "rowCnt 불일치",
                               "detail": "속성 %d ≠ 실제 %d" % (attr_r, rows)})
                bad = True
            if attr_c is not None and cols and attr_c != cols:
                issues.append({"table": i, "kind": "colCnt 불일치",
                               "detail": "속성 %d ≠ 실제 %d" % (attr_c, cols)})
                bad = True
            if dups:
                issues.append({"table": i, "kind": "셀 주소 중복",
                               "detail": str(dups[:5])})
            if rows and addr_rows and addr_rows != rows:
                issues.append({"table": i, "kind": "주소/행수 불일치",
                               "detail": "주소기반 %d행, tr %d개 — 수동 확인 필요"
                               % (addr_rows, rows)})
            if fix and bad and not dups and addr_rows == rows:
                fix_targets.setdefault(sec, []).append(((s, e), hp))
        fixed = 0
        # 뒤 위치부터 고쳐서 앞 위치가 안 밀리게
        for sec, targets in fix_targets.items():
            xml = self.files[sec].decode("utf-8")
            for (s, e), hp in sorted(targets, reverse=True):
                xml = xml[:s] + self._resync_counts_chunk(xml[s:e], hp) \
                    + xml[e:]
                fixed += 1
            self.files[sec] = xml.encode("utf-8")
        return issues, fixed

    def copy_row(self, table_index, row, count=1):
        """표의 특정 행을 복제해 바로 뒤에 count번 삽입한다.
        rowAddr/rowCnt를 자동 보정하고, 병합 셀(rowSpan>1)이
        있는 행은 거부한다 (안전한 단순 행만 복제)."""
        tb = self.tables()[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        ts, te = tb["span"]
        blk = xml[ts:te]
        inner_start = ts + blk.find(">") + 1
        trs = list(re.finditer(r"<%s:tr>.*?</%s:tr>" % (hp, hp),
                               xml[inner_start:te], re.DOTALL))
        if not (0 <= row < len(trs)):
            raise IndexError("행 번호는 0~%d 사이여야 합니다." % (len(trs) - 1))
        tr = trs[row]
        tr_text = xml[inner_start + tr.start():inner_start + tr.end()]
        if re.search(r'rowSpan="(?!1")\d', tr_text) or \
           any(int(m.group(1)) > 1 for m in
               re.finditer(r'rowSpan="(\d+)"', tr_text)):
            raise ValueError("병합된(rowSpan>1) 행은 복제할 수 없습니다.")
        insert_at = inner_start + tr.end()
        clones = []
        for k in range(1, count + 1):
            c = re.sub(r'rowAddr="\d+"',
                      lambda m, k=k: 'rowAddr="%d"' % (row + k), tr_text)
            clones.append(c)
        clone = "".join(clones)
        new_xml = xml[:insert_at] + clone + xml[insert_at:]
        # 뒤따르던 원래 행들의 rowAddr을 count만큼 뒤로 밀기
        tail_start = insert_at + len(clone)
        def bump(m):
            r = int(m.group(1))
            return 'rowAddr="%d"' % (r + count) if r > row else m.group(0)
        new_xml = new_xml[:tail_start] + \
            re.sub(r'rowAddr="(\d+)"', bump, new_xml[tail_start:te + len(clone)]) + \
            new_xml[te + len(clone):]
        # rowCnt 갱신 + 뒤따르는 행들의 rowAddr을 count만큼 밀기
        rm = re.search(r'rowCnt="(\d+)"', new_xml[ts:te])
        if rm:
            old_cnt = int(rm.group(1))
            new_xml = (new_xml[:ts] +
                      new_xml[ts:te].replace('rowCnt="%d"' % old_cnt,
                                             'rowCnt="%d"' % (old_cnt + count), 1)
                      + new_xml[te:])
        self.files[sec] = new_xml.encode("utf-8")
        return count

    def del_row(self, table_index, row):
        """표에서 행 삭제. 세로 병합 셀은 폭을 1 줄여 안전하게 처리."""
        self._del_line(table_index, row, "row")

    def del_col(self, table_index, col):
        """표에서 열 삭제. 가로 병합 셀은 폭을 1 줄여 안전하게 처리."""
        self._del_line(table_index, col, "col")

    # ---------- 표 통째 삭제 ----------
    def set_col_widths(self, table_index, widths):
        """표의 열 폭을 재설정한다. widths: 열별 폭 리스트(HWPUNIT).
        각 셀의 cellSz width를 colAddr·colSpan에 따라 다시 계산한다.
        표 전체 폭과 합이 같아야 칸 균형이 맞는다."""
        tb = self.tables()[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        ts, te = tb["span"]
        blk = xml[ts:te]
        # 중첩표 범위(건드리지 않음)
        inner = blk[blk.find(">") + 1:]
        offset = ts + blk.find(">") + 1
        nested = [(s + offset, e + offset)
                  for s, e in _find_elements(inner, "%s:tbl" % hp)]

        out = [xml[:ts]]
        pos = ts
        pat = re.compile(
            r'(<hp:cellAddr[^>]*colAddr="(\d+)"[^>]*/>\s*'
            r'<hp:cellSpan[^>]*colSpan="(\d+)"[^>]*/>\s*'
            r'<hp:cellSz[^>]*width=")(\d+)(")'.replace("hp:", "%s:" % hp))
        for m in pat.finditer(xml, ts, te):
            if any(s <= m.start() < e for s, e in nested):
                continue
            ca, cs = int(m.group(2)), int(m.group(3))
            w = sum(widths[ca:ca + cs])
            out.append(xml[pos:m.start()] + m.group(1) + str(w) + m.group(5))
            pos = m.end()
        out.append(xml[pos:])
        self.files[sec] = "".join(out).encode("utf-8")
        return len(out) - 1

    def set_row_heights(self, table_index, heights):
        """행 높이(최소 높이) 재설정. heights: {행번호: 높이(HWPUNIT)}.
        cellSz height는 최소 높이로 동작하므로 내용이 많으면 한글이
        자동으로 늘린다 — 줄여도 안전. 빈 공간을 줄여 아래 내용을
        끌어올릴 때 쓴다."""
        tb = self.tables()[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        ts, te = tb["span"]
        blk = xml[ts:te]
        inner = blk[blk.find(">") + 1:]
        offset = ts + blk.find(">") + 1
        nested = [(s + offset, e + offset)
                  for s, e in _find_elements(inner, "%s:tbl" % hp)]
        pat = re.compile(
            (r'(<hp:cellAddr[^>]*rowAddr="(\d+)"[^>]*/>\s*'
             r'<hp:cellSpan[^>]*/>\s*'
             r'<hp:cellSz[^>]*height=")(\d+)(")').replace(
                "hp:", "%s:" % hp))
        out = [xml[:ts]]
        pos = ts
        cnt = 0
        for m in pat.finditer(xml, ts, te):
            if any(s <= m.start() < e for s, e in nested):
                continue
            r = int(m.group(2))
            if r in heights:
                out.append(xml[pos:m.start()] + m.group(1)
                           + str(heights[r]) + m.group(4))
                pos = m.end()
                cnt += 1
        out.append(xml[pos:])
        self.files[sec] = "".join(out).encode("utf-8")
        return cnt

    def set_table_pagebreak(self, table_index, mode="CELL"):
        """표의 쪽 경계 나눔 방식 설정.
        CELL=셀 단위로 나눔(표가 페이지에 걸쳐 이어짐),
        NONE=나누지 않음(통째로 다음 쪽 이동), TABLE=표 단위.
        빈 공간에 표 앞부분을 끌어올리려면 CELL로 바꾼다."""
        tb = self.tables()[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        ts, te = tb["span"]
        head_end = xml.find(">", ts) + 1
        head = xml[ts:head_end]
        if 'pageBreak="' in head:
            new_head = re.sub(r'pageBreak="[^"]*"',
                              'pageBreak="%s"' % mode, head)
        else:
            new_head = head[:-1] + ' pageBreak="%s">' % mode
        self.files[sec] = (xml[:ts] + new_head
                           + xml[head_end:]).encode("utf-8")
        return mode

    def copy_table(self, table_index):
        """표를 복제해 바로 뒤에 삽입한다 (표를 감싼 문단째 복제 —
        lineseg 포함이라 렌더링 안전). 큰 표를 두 개로 나눠
        페이지 여백을 채울 때 쓴다. 반환: 새 표 인덱스(원본+1)."""
        tb = self.tables()[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        ts, te = tb["span"]
        # 표를 감싼 최소 문단 찾기
        ps = xml.rfind("<%s:p " % hp, 0, ts)
        pe = xml.find("</%s:p>" % hp, te) + len("</%s:p>" % hp)
        if ps < 0 or pe <= ts:
            raise ValueError("표를 감싼 문단을 찾지 못했습니다.")
        block = xml[ps:pe]
        self.files[sec] = (xml[:pe] + block + xml[pe:]).encode("utf-8")
        return table_index + 1

    def del_table(self, table_index):
        """표를 통째로 삭제. 표만 담고 있는 문단이면 문단째 제거해
        빈 줄도 안 남긴다."""
        tables = self.tables()
        if not (0 <= table_index < len(tables)):
            raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
        tb = tables[table_index]
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "p")
        s, e = tb["span"]

        # 이 표를 감싸는 가장 안쪽 문단 찾기 (깊이 추적으로 정확한 경계)
        wrap = None
        for ps, pe in _find_elements(xml, "%s:p" % hp):
            if ps < s and e <= pe:
                if wrap is None or (pe - ps) < (wrap[1] - wrap[0]):
                    wrap = (ps, pe)
        if wrap:
            ps, pe = wrap
            rest = xml[ps:s] + xml[e:pe]
            tpat = _t_pattern(_detect_prefix(xml, "t"))
            rest_text = "".join(t.group(2) for t in tpat.finditer(rest))
            if not rest_text.strip():
                s, e = ps, pe          # 문단째 삭제
        self.files[sec] = (xml[:s] + xml[e:]).encode("utf-8")

    # ---------- 문단 삭제 ----------
    def del_para(self, index):
        """최상위 문단 삭제. 표 안(셀) 문단은 구조가 깨질 수 있어 거부
        (셀 문단은 set-cell로 비우면 됨)."""
        paras = self.paragraphs()
        if not (0 <= index < len(paras)):
            raise IndexError("문단 번호는 0~%d 사이여야 합니다." % (len(paras) - 1))
        sec, (start, end), _, text = paras[index]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "p")
        # 정규식 스팬은 문단 안에 중첩 문단(표 셀)이 있으면 끝을 잘못 잡으므로
        # 깊이 추적으로 균형 잡힌 진짜 경계를 다시 찾는다
        p_spans = _find_elements(xml, "%s:p" % hp)
        true_span = next((sp for sp in p_spans if sp[0] == start), None)
        if true_span:
            start, end = true_span
        tbl_spans = _find_elements(xml, "%s:tbl" % _detect_prefix(xml, "tbl"))
        if _inside_any((start, end), tbl_spans):
            raise ValueError(
                "문단 %d은 표 안(셀)의 문단이라 삭제하면 표가 깨질 수 있습니다. "
                "set-cell로 내용을 비우세요." % index)
        self.files[sec] = (xml[:start] + xml[end:]).encode("utf-8")
        return text

    # ---------- 셀 글자 크기 / 겹침 해결 ----------
    def _header_name(self):
        for n in self.names:
            if n.endswith("header.xml"):
                return n
        raise ValueError("header.xml을 찾지 못했습니다.")

    @staticmethod
    def _strip_lineseg(chunk, hp):
        """줄배치 캐시(linesegarray) 제거 → 한글이 열 때 새로 계산해
        글자 겹침이 풀린다."""
        pat = (r"<%s:linesegarray\b[^>]*/>|<%s:linesegarray\b.*?</%s:linesegarray>"
               % (hp, hp, hp))
        return re.sub(pat, "", chunk, flags=re.DOTALL)

    def _clone_char_pr(self, src_id, new_height):
        """header.xml에서 charPr(src_id)를 복제해 글자 크기만 바꾼
        새 charPr을 만들고 그 id를 반환. 같은 요청은 캐시로 재사용."""
        if not hasattr(self, "_font_cache"):
            self._font_cache = {}
        key = (src_id, new_height)
        if key in self._font_cache:
            return self._font_cache[key]
        hname = self._header_name()
        h = self.files[hname].decode("utf-8")
        hh = _detect_prefix(h, "charPr")
        spans = _find_elements(h, "%s:charPr" % hh)
        src_span = None
        for s_, e_ in spans:
            m = re.match(r"<%s:charPr\b[^>]*\bid=\"(\d+)\"" % hh, h[s_:e_])
            if m and m.group(1) == str(src_id):
                src_span = (s_, e_)
                break
        if src_span is None:
            raise ValueError("charPr id=%s 를 header.xml에서 찾지 못했습니다."
                             % src_id)
        ids = [int(x) for x in
               re.findall(r"<%s:charPr\b[^>]*\bid=\"(\d+)\"" % hh, h)]
        new_id = max(ids) + 1
        clone = h[src_span[0]:src_span[1]]
        clone = re.sub(r'(\bid=")(\d+)(")',
                       lambda m: m.group(1) + str(new_id) + m.group(3),
                       clone, count=1)
        clone = re.sub(r'(\bheight=")(\d+)(")',
                       lambda m: m.group(1) + str(new_height) + m.group(3),
                       clone, count=1)
        h = h[:src_span[1]] + clone + h[src_span[1]:]
        h = re.sub(r'(<%s:charProperties\b[^>]*\bitemCnt=")(\d+)(")' % hh,
                   lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3),
                   h, count=1)
        self.files[hname] = h.encode("utf-8")
        self._font_cache[key] = new_id
        return new_id

    def _cell_chunk(self, table_index, row, col):
        tables = self.tables()
        if not (0 <= table_index < len(tables)):
            raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
        tb = tables[table_index]
        target = next((c for c in tb["cells"]
                       if c["row"] == row and c["col"] == col), None)
        if target is None:
            raise IndexError("표 %d에 (행 %d, 열 %d) 셀이 없습니다."
                             % (table_index, row, col))
        return tb, target

    def cell_font(self, table_index, row, col, pt):
        """셀 안 글자 크기를 pt로 변경 (그 셀만, 다른 셀 영향 없음).
        줄배치 캐시도 함께 지워 겹침을 방지."""
        tb, target = self._cell_chunk(table_index, row, col)
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        cs, ce = target["span"]
        chunk = xml[cs:ce]
        spans = _find_elements(chunk, "%s:tbl" % hp)
        outer = max(spans, key=lambda sp: sp[1] - sp[0]) if spans else None
        nested_local = [sp for sp in spans if sp != outer] if outer else spans

        run_re = re.compile(r'(<%s:run\b[^>]*\bcharPrIDRef=")(\d+)(")' % hp)
        runs = [m for m in run_re.finditer(chunk)
                if not _inside_any((m.start(), m.end()), nested_local)]
        if not runs:
            raise ValueError("이 셀에서 글자 속성(run)을 찾지 못했습니다.")
        new_height = int(round(pt * 100))
        pieces, pos = [], 0
        for m in runs:
            new_id = self._clone_char_pr(int(m.group(2)), new_height)
            pieces.append(chunk[pos:m.start(2)])
            pieces.append(str(new_id))
            pos = m.end(2)
        pieces.append(chunk[pos:])
        chunk = self._strip_lineseg("".join(pieces), hp)
        self.files[sec] = (xml[:cs] + chunk + xml[ce:]).encode("utf-8")
        return new_height

    def _current_cell_font(self, chunk, hp):
        """셀 첫 run의 charPr 글자 크기(1/100pt)를 header에서 읽어옴."""
        m = re.search(r'<%s:run\b[^>]*\bcharPrIDRef="(\d+)"' % hp, chunk)
        if not m:
            return 1000
        h = self.files[self._header_name()].decode("utf-8")
        hh = _detect_prefix(h, "charPr")
        cm = re.search(r'<%s:charPr\b[^>]*\bid="%s"[^>]*\bheight="(\d+)"'
                       % (hh, m.group(1)), h)
        return int(cm.group(1)) if cm else 1000

    def fit_cell(self, table_index, row, col, min_pt=6.0):
        """셀 폭·높이 대비 글자량을 계산해서, 넘치면 글자 크기를
        자동으로 줄인다(최소 min_pt). 맞으면 겹침 캐시만 갱신."""
        tb, target = self._cell_chunk(table_index, row, col)
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        cs, ce = target["span"]
        chunk = xml[cs:ce]

        wm = re.search(r'<%s:cellSz\b[^>]*\bwidth="(\d+)"' % hp, chunk)
        hm = re.search(r'<%s:cellSz\b[^>]*\bheight="(\d+)"' % hp, chunk)
        width = int(wm.group(1)) if wm else 8000
        height = int(hm.group(1)) if hm else 2000
        cur = self._current_cell_font(chunk, hp)

        text = target["text"]
        def units(line):
            return sum(1.0 if ord(ch) > 0x2E7F else 0.55 for ch in line)
        lines = text.split("\n")
        usable_w = max(width - 1000, 1000)   # 좌우 여백 감안
        usable_h = max(height - 566, 1000)   # 상하 여백 감안

        def fits(H):
            per_line = usable_w / H          # 전각 기준 한 줄 글자 수
            need = 0
            for l in lines:
                u = units(l)
                need += max(1, int(-(-u // per_line)))
            # 한글에서 행은 내용에 따라 세로로 늘어나므로,
            # 원래 높이의 2배까지 커지는 것을 허용하고 크기를 정한다
            return need * H * 1.7 <= usable_h * 2.0

        if fits(cur):
            return cur / 100.0
        H = cur
        floor = int(min_pt * 100)
        while H > floor and not fits(H):
            H -= 50                          # 0.5pt씩 축소
        return self.cell_font(table_index, row, col, H / 100.0) / 100.0

    def para_font(self, index, pt):
        """문단 안 모든 글자를 같은 크기·모양으로 통일.
        (첫 run의 속성을 기준으로 크기만 pt로 바꾼 통일본을 만들어
        문단 전체에 적용. 크기가 뒤섞인 문단 정리용.)
        문단 안에 표가 있으면 표 내부는 건드리지 않음."""
        paras = self.paragraphs()
        if not (0 <= index < len(paras)):
            raise IndexError("문단 번호는 0~%d 사이여야 합니다." % (len(paras) - 1))
        sec, (start, end), _, _ = paras[index]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "p")
        # 균형 잡힌 진짜 문단 경계
        true_span = next((sp for sp in _find_elements(xml, "%s:p" % hp)
                          if sp[0] == start), None)
        if true_span:
            start, end = true_span
        chunk = xml[start:end]
        # 문단 안 표 내부는 제외
        tbl_local = _find_elements(chunk, "%s:tbl" % hp)
        run_re = re.compile(r'(<%s:run\b[^>]*\bcharPrIDRef=")(\d+)(")' % hp)
        runs = [m for m in run_re.finditer(chunk)
                if not _inside_any((m.start(), m.end()), tbl_local)]
        if not runs:
            raise ValueError("문단 %d에서 글자 속성(run)을 찾지 못했습니다." % index)
        base = int(runs[0].group(2))
        new_id = self._clone_char_pr(base, int(round(pt * 100)))
        pieces, pos = [], 0
        for m in runs:
            pieces.append(chunk[pos:m.start(2)])
            pieces.append(str(new_id))
            pos = m.end(2)
        pieces.append(chunk[pos:])
        chunk = "".join(pieces)
        # 표 내부를 피해서 줄배치 캐시 제거
        tbl_local2 = _find_elements(chunk, "%s:tbl" % hp)
        ls_re = re.compile(
            r"<%s:linesegarray\b[^>]*/>|<%s:linesegarray\b.*?</%s:linesegarray>"
            % (hp, hp, hp), re.DOTALL)
        pieces, pos = [], 0
        for m in ls_re.finditer(chunk):
            if _inside_any((m.start(), m.end()), tbl_local2):
                continue
            pieces.append(chunk[pos:m.start()])
            pos = m.end()
        pieces.append(chunk[pos:])
        chunk = "".join(pieces)
        self.files[sec] = (xml[:start] + chunk + xml[end:]).encode("utf-8")
        return new_id

    # ---------- 스타일 조회/복사/검사 (공문서 원칙: 표 안 통일) ----------
    def _char_info(self, charpr_id):
        """charPr id → (글꼴명, 크기pt, 장평%)"""
        h = self.files[self._header_name()].decode("utf-8")
        hh = _detect_prefix(h, "charPr")
        span = None
        for s_, e_ in _find_elements(h, "%s:charPr" % hh):
            m = re.match(r"<%s:charPr\b[^>]*\bid=\"%s\"" % (hh, charpr_id),
                         h[s_:e_])
            if m:
                span = h[s_:e_]
                break
        if span is None:
            return ("?", 0, 100)
        hm = re.search(r'\bheight="(\d+)"', span)
        size = int(hm.group(1)) / 100 if hm else 0
        rm = re.search(r"<%s:ratio\b[^>]*\bhangul=\"(\d+)\"" % hh, span)
        ratio = int(rm.group(1)) if rm else 100
        fm = re.search(r"<%s:fontRef\b[^>]*\bhangul=\"(\d+)\"" % hh, span)
        font = "?"
        if fm:
            nm = re.search(r"<%s:font\b[^>]*\bid=\"%s\"[^>]*\bface=\"([^\"]+)\""
                           % (hh, fm.group(1)), h)
            if nm:
                font = nm.group(1)
        return (font, size, ratio)

    def _para_align(self, parapr_id):
        """paraPr id → 정렬(한글)"""
        h = self.files[self._header_name()].decode("utf-8")
        hh = _detect_prefix(h, "paraPr")
        for s_, e_ in _find_elements(h, "%s:paraPr" % hh):
            chunk = h[s_:e_]
            if re.match(r"<%s:paraPr\b[^>]*\bid=\"%s\"" % (hh, parapr_id),
                        chunk):
                am = re.search(r"<%s:align\b[^>]*\bhorizontal=\"(\w+)\"" % hh,
                               chunk)
                if am:
                    return _ALIGN_KO.get(am.group(1), am.group(1))
                return "양쪽(기본)"
        return "?"

    def _cell_style_ids(self, chunk, hp):
        """셀 chunk에서 (첫 run charPrIDRef, 첫 문단 paraPrIDRef)"""
        rm = re.search(r'<%s:run\b[^>]*\bcharPrIDRef="(\d+)"' % hp, chunk)
        pm = re.search(r'<%s:p\b[^>]*\bparaPrIDRef="(\d+)"' % hp, chunk)
        return (rm.group(1) if rm else None, pm.group(1) if pm else None)

    def cell_style(self, table_index, row, col):
        """셀의 글꼴·크기·장평·정렬 조회"""
        tb, target = self._cell_chunk(table_index, row, col)
        xml = self.files[tb["sec"]].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        cs, ce = target["span"]
        cid, pid = self._cell_style_ids(xml[cs:ce], hp)
        font, size, ratio = self._char_info(cid) if cid else ("?", 0, 100)
        align = self._para_align(pid) if pid else "?"
        return {"font": font, "size": size, "ratio": ratio,
                "align": align, "charPr": cid, "paraPr": pid}

    def copy_style(self, table_index, row, col, ref_row, ref_col):
        """참조 셀의 글꼴·크기·정렬을 대상 셀에 그대로 적용
        (공문서 원칙: 표 안 글꼴·포인트 통일). 내용은 그대로 둠."""
        tb, ref = self._cell_chunk(table_index, ref_row, ref_col)
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        rcid, rpid = self._cell_style_ids(
            xml[ref["span"][0]:ref["span"][1]], hp)
        if not rcid:
            raise ValueError("참조 셀에서 글자 속성을 찾지 못했습니다.")
        target = next((c for c in tb["cells"]
                       if c["row"] == row and c["col"] == col), None)
        if target is None:
            raise IndexError("표 %d에 (행 %d, 열 %d) 셀이 없습니다."
                             % (table_index, row, col))
        cs, ce = target["span"]
        chunk = xml[cs:ce]
        spans = _find_elements(chunk, "%s:tbl" % hp)
        outer = max(spans, key=lambda sp: sp[1] - sp[0]) if spans else None
        nested_local = [sp for sp in spans if sp != outer] if outer else spans
        run_re = re.compile(r'(<%s:run\b[^>]*\bcharPrIDRef=")(\d+)(")' % hp)
        pieces, pos = [], 0
        for m in run_re.finditer(chunk):
            if _inside_any((m.start(), m.end()), nested_local):
                continue
            pieces.append(chunk[pos:m.start(2)])
            pieces.append(rcid)
            pos = m.end(2)
        pieces.append(chunk[pos:])
        chunk = "".join(pieces)
        if rpid:
            p_re = re.compile(r'(<%s:p\b[^>]*\bparaPrIDRef=")(\d+)(")' % hp)
            pieces, pos = [], 0
            for m in p_re.finditer(chunk):
                if _inside_any((m.start(), m.end()), nested_local):
                    continue
                pieces.append(chunk[pos:m.start(2)])
                pieces.append(rpid)
                pos = m.end(2)
            pieces.append(chunk[pos:])
            chunk = "".join(pieces)
        chunk = self._strip_lineseg(chunk, hp)
        self.files[sec] = (xml[:cs] + chunk + xml[ce:]).encode("utf-8")
        return self._char_info(rcid)

    # ---------- 문단 세부 속성 (줄간격·여백·들여쓰기) ----------
    def _para_details(self, parapr_id):
        """paraPr id → 줄간격/들여쓰기/여백 상세 (단위: pt)"""
        h = self.files[self._header_name()].decode("utf-8")
        hh = _detect_prefix(h, "paraPr")
        for s_, e_ in _find_elements(h, "%s:paraPr" % hh):
            chunk = h[s_:e_]
            if not re.match(r"<%s:paraPr\b[^>]*\bid=\"%s\"" % (hh, parapr_id),
                            chunk):
                continue
            out = {"align": self._para_align(parapr_id)}
            sm = re.search(r'<%s:lineSpacing\b[^>]*\btype="(\w+)"[^>]*\bvalue="(-?\d+)"'
                           % hh, chunk)
            if sm:
                t, v = sm.group(1), int(sm.group(2))
                out["spacing"] = "%d%%" % v if t == "PERCENT" \
                    else "%.1fpt(%s)" % (v / 100, t)
            for tag, key in [("intent", "들여쓰기"), ("left", "왼쪽여백"),
                             ("right", "오른쪽여백"), ("prev", "문단위"),
                             ("next", "문단아래")]:
                m = re.search(r'<\w+:%s\b[^>]*\bvalue="(-?\d+)"' % tag, chunk)
                if m:
                    out[key] = int(m.group(1)) / 100.0
            return out
        return {}

    def _clone_para_pr(self, src_id, align=None, spacing=None, indent=None,
                       left=None, right=None, prev=None, nxt=None):
        """paraPr(src_id)를 복제해 지정한 속성만 바꾼 새 paraPr id 반환.
        margin/lineSpacing이 신·구버전 분기로 2번 나오므로 모두 변경."""
        if not hasattr(self, "_para_cache"):
            self._para_cache = {}
        key = (src_id, align, spacing, indent, left, right, prev, nxt)
        if key in self._para_cache:
            return self._para_cache[key]
        hname = self._header_name()
        h = self.files[hname].decode("utf-8")
        hh = _detect_prefix(h, "paraPr")
        src_span = None
        for s_, e_ in _find_elements(h, "%s:paraPr" % hh):
            if re.match(r"<%s:paraPr\b[^>]*\bid=\"%s\"" % (hh, src_id),
                        h[s_:e_]):
                src_span = (s_, e_)
                break
        if src_span is None:
            raise ValueError("paraPr id=%s 를 header.xml에서 찾지 못했습니다."
                             % src_id)
        ids = [int(x) for x in
               re.findall(r"<%s:paraPr\b[^>]*\bid=\"(\d+)\"" % hh, h)]
        new_id = max(ids) + 1
        clone = h[src_span[0]:src_span[1]]
        clone = re.sub(r'(\bid=")(\d+)(")',
                       lambda m: m.group(1) + str(new_id) + m.group(3),
                       clone, count=1)
        if align:
            en = _ALIGN_EN.get(align, align.upper())
            clone = re.sub(r'(<%s:align\b[^>]*\bhorizontal=")(\w+)(")' % hh,
                           lambda m: m.group(1) + en + m.group(3), clone)
        if spacing is not None:
            clone = re.sub(
                r'(<%s:lineSpacing\b[^>]*\btype=")(\w+)(")' % hh,
                lambda m: m.group(1) + "PERCENT" + m.group(3), clone)
            clone = re.sub(
                r'(<%s:lineSpacing\b[^>]*\bvalue=")(-?\d+)(")' % hh,
                lambda m: m.group(1) + str(int(spacing)) + m.group(3), clone)
        for tag, val in [("intent", indent), ("left", left),
                         ("right", right), ("prev", prev), ("next", nxt)]:
            if val is not None:
                clone = re.sub(
                    r'(<(\w+):%s\b[^>]*\bvalue=")(-?\d+)(")' % tag,
                    lambda m: m.group(1) + str(int(round(val * 100)))
                    + m.group(4),
                    clone)
        h = h[:src_span[1]] + clone + h[src_span[1]:]
        h = re.sub(r'(<%s:paraProperties\b[^>]*\bitemCnt=")(\d+)(")' % hh,
                   lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3),
                   h, count=1)
        self.files[hname] = h.encode("utf-8")
        self._para_cache[key] = new_id
        return new_id

    def para_prop(self, index, **changes):
        """문단의 줄간격·정렬·들여쓰기·여백 변경 (그 문단만)."""
        paras = self.paragraphs()
        if not (0 <= index < len(paras)):
            raise IndexError("문단 번호는 0~%d 사이여야 합니다." % (len(paras) - 1))
        sec, (start, end), _, _ = paras[index]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "p")
        true_span = next((sp for sp in _find_elements(xml, "%s:p" % hp)
                          if sp[0] == start), None)
        if true_span:
            start, end = true_span
        chunk = xml[start:end]
        pm = re.match(r'<%s:p\b[^>]*\bparaPrIDRef="(\d+)"' % hp, chunk)
        if not pm:
            raise ValueError("문단 %d에서 문단 속성을 찾지 못했습니다." % index)
        new_id = self._clone_para_pr(pm.group(1), **changes)
        chunk = re.sub(r'(\bparaPrIDRef=")(\d+)(")',
                       lambda m: m.group(1) + str(new_id) + m.group(3),
                       chunk, count=1)
        tbl_local = _find_elements(chunk, "%s:tbl" % hp)
        ls_re = re.compile(
            r"<%s:linesegarray\b[^>]*/>|<%s:linesegarray\b.*?</%s:linesegarray>"
            % (hp, hp, hp), re.DOTALL)
        pieces, pos = [], 0
        for m in ls_re.finditer(chunk):
            if _inside_any((m.start(), m.end()), tbl_local):
                continue
            pieces.append(chunk[pos:m.start()])
            pos = m.end()
        pieces.append(chunk[pos:])
        chunk = "".join(pieces)
        self.files[sec] = (xml[:start] + chunk + xml[end:]).encode("utf-8")
        return new_id

    def cell_prop(self, table_index, row, col, **changes):
        """셀 안 모든 문단의 줄간격·정렬·여백 변경 (그 셀만)."""
        tb, target = self._cell_chunk(table_index, row, col)
        sec = tb["sec"]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        cs, ce = target["span"]
        chunk = xml[cs:ce]
        spans = _find_elements(chunk, "%s:tbl" % hp)
        outer = max(spans, key=lambda sp: sp[1] - sp[0]) if spans else None
        nested_local = [sp for sp in spans if sp != outer] if outer else spans
        p_re = re.compile(r'(<%s:p\b[^>]*\bparaPrIDRef=")(\d+)(")' % hp)
        targets = [m for m in p_re.finditer(chunk)
                   if not _inside_any((m.start(), m.end()), nested_local)]
        if not targets:
            raise ValueError("이 셀에서 문단 속성을 찾지 못했습니다.")
        new_id = self._clone_para_pr(targets[0].group(2), **changes)
        pieces, pos = [], 0
        for m in targets:
            pieces.append(chunk[pos:m.start(2)])
            pieces.append(str(new_id))
            pos = m.end(2)
        pieces.append(chunk[pos:])
        chunk = self._strip_lineseg("".join(pieces), hp)
        self.files[sec] = (xml[:cs] + chunk + xml[ce:]).encode("utf-8")
        return new_id

    def table_style(self, table_index):
        """표의 본문 셀에서 (charPr, paraPr, borderFill) 추출 —
        새 표를 만들 때 기존 표 스타일 상속용."""
        tables = self.tables()
        if not (0 <= table_index < len(tables)):
            raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
        tb = tables[table_index]
        xml = self.files[tb["sec"]].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        # 본문 셀 우선(행1), 없으면 첫 셀
        cand = next((c for c in tb["cells"] if c["row"] == 1), tb["cells"][0])
        cs, ce = cand["span"]
        chunk = xml[cs:ce]
        cid, pid = self._cell_style_ids(chunk, hp)
        bm = re.search(r'<%s:tc\b[^>]*\bborderFillIDRef="(\d+)"' % hp, chunk)
        return {"charPr": cid or "0", "paraPr": pid or "0",
                "borderFill": bm.group(1) if bm else None}

    def check_table(self, table_index):
        """표 안 글꼴·크기·정렬 일관성 검사.
        다수(대표) 스타일과 다른 셀을 보고. (공문서 원칙 6 근거)"""
        tables = self.tables()
        if not (0 <= table_index < len(tables)):
            raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
        tb = tables[table_index]
        xml = self.files[tb["sec"]].decode("utf-8")
        hp = _detect_prefix(xml, "tbl")
        styles = {}
        for c in tb["cells"]:
            cs, ce = c["span"]
            cid, pid = self._cell_style_ids(xml[cs:ce], hp)
            if cid is None:
                continue
            font, size, ratio = self._char_info(cid)
            align = self._para_align(pid) if pid else "?"
            key = (font, size, align)
            styles.setdefault(key, []).append((c["row"], c["col"]))
        if not styles:
            return {"dominant": None, "deviations": []}
        dominant = max(styles.items(), key=lambda kv: len(kv[1]))[0]
        deviations = [(key, cells) for key, cells in styles.items()
                      if key != dominant]
        return {"dominant": dominant, "count": len(styles[dominant]),
                "deviations": deviations}

    # ---------- 텍스트 ----------
    def replace_text(self, old, new):
        count = 0
        for sec in self.sections:
            xml = self.files[sec].decode("utf-8")
            pat = _t_pattern(_detect_prefix(xml, "t"))

            def repl(m):
                nonlocal count
                raw = m.group(2)
                # <hp:t> 내부에 <hp:tab/> 같은 태그가 있을 수 있으므로
                # 태그는 보존하고 텍스트 조각만 치환한다
                parts = re.split(r'(<[^>]+>)', raw)
                changed = False
                for j, part in enumerate(parts):
                    if part.startswith('<'):
                        continue
                    txt = _unescape(part)
                    if old in txt:
                        count += txt.count(old)
                        parts[j] = escape(txt.replace(old, new))
                        changed = True
                if changed:
                    return m.group(1) + ''.join(parts) + m.group(3)
                return m.group(0)

            self.files[sec] = pat.sub(repl, xml).encode("utf-8")
        return count

    def replace_regex(self, pattern, repl):
        """정규식으로 문서 전체 찾아 바꾸기 (표 안 포함).
        replace_text와 동일하게 <hp:t> 텍스트 노드만 대상으로 하고,
        인라인 태그(tab/lineBreak 등)는 보존한다. 텍스트 조각을 unescape한
        상태에서 re.sub을 적용하므로, 예: 앞뒤 문맥을 보는 lookbehind로
        '2026학년도' 안의 '6학년'은 건드리지 않게 안전 치환할 수 있다."""
        rx = re.compile(pattern)
        count = 0
        for sec in self.sections:
            xml = self.files[sec].decode("utf-8")
            pat = _t_pattern(_detect_prefix(xml, "t"))

            def repl_node(m):
                nonlocal count
                raw = m.group(2)
                parts = re.split(r'(<[^>]+>)', raw)   # 인라인 태그 보존
                changed = False
                for j, part in enumerate(parts):
                    if part.startswith('<'):
                        continue
                    txt = _unescape(part)
                    new_txt, n = rx.subn(repl, txt)
                    if n:
                        count += n
                        parts[j] = escape(new_txt)
                        changed = True
                if changed:
                    return m.group(1) + ''.join(parts) + m.group(3)
                return m.group(0)

            self.files[sec] = pat.sub(repl_node, xml).encode("utf-8")
        return count

    def set_paragraph(self, index, new_text):
        paras = self.paragraphs()
        if not (0 <= index < len(paras)):
            raise IndexError("문단 번호는 0~%d 사이여야 합니다." % (len(paras) - 1))
        sec, (start, end), _, _ = paras[index]
        xml = self.files[sec].decode("utf-8")
        para = xml[start:end]
        tpat = _t_pattern(_detect_prefix(xml, "t"))
        matches = list(tpat.finditer(para))
        if not matches:
            raise ValueError("이 문단에는 텍스트 노드가 없습니다.")
        pieces, pos = [], 0
        for i, m in enumerate(matches):
            pieces.append(para[pos:m.start()])
            body = escape(new_text) if i == 0 else ""
            pieces.append(m.group(1) + body + m.group(3))
            pos = m.end()
        pieces.append(para[pos:])
        self.files[sec] = (xml[:start] + "".join(pieces) + xml[end:]).encode("utf-8")

    def add_paragraph(self, new_text):
        sec = self.sections[-1]
        xml = self.files[sec].decode("utf-8")
        hp = _detect_prefix(xml, "p")
        # 표 안이 아닌 최상위 문단만 복제 대상으로
        tbl_spans = _find_elements(xml, "%s:tbl" % hp)
        cands = [m for m in _p_pattern(hp).finditer(xml)
                 if not _inside_any(m.span(), tbl_spans)]
        if not cands:
            raise ValueError("복제할 기존 문단이 없습니다.")
        last = cands[-1]
        clone = last.group(0)
        tpat = _t_pattern(_detect_prefix(xml, "t"))
        tms = list(tpat.finditer(clone))
        if tms:
            pieces, pos = [], 0
            for i, m in enumerate(tms):
                pieces.append(clone[pos:m.start()])
                body = escape(new_text) if i == 0 else ""
                pieces.append(m.group(1) + body + m.group(3))
                pos = m.end()
            pieces.append(clone[pos:])
            clone = "".join(pieces)
        clone = re.sub(r'(\sid=")(\d+)(")',
                       lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3),
                       clone, count=1)
        self.files[sec] = (xml[:last.end()] + clone + xml[last.end():]).encode("utf-8")


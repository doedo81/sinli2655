"""autotable — 표 자동 레이아웃 (Phase A 핵심).

사용자가 행·열·폭을 계산하지 않는다. 내용만 채우고 autofit_table을 부르면
엔진이 측정→배분→맞춤을 자동 수행한다. 핵심 원칙:

  "글자가 긴 셀만 그 칸(열)을 더 넓게" — 표 전체 폭은 유지한 채,
  열별 최장 내용에 비례해 폭을 재분배한다.

넘침 처리 우선순위:
  ① 그 열을 넓힌다(표 폭 여유가 있으면)      ← 기본
  ② 행 높이를 키운다(줄바꿈 허용)
  ③ 마지막 수단으로만 그 셀 글자 축소(fit_cell)

기존 HwpxDoc 메서드(set_col_widths / set_row_heights / fit_cell / verify)를
오케스트레이션할 뿐, 저수준 XML은 그 검증된 코드가 처리한다.

단위: HWPUNIT (1pt = 100 HWPUNIT). 글꼴 height 값(1/100pt)이 곧 전각 한 글자
폭(HWPUNIT)에 대응하므로, 전각=height, 반각=0.55×height 로 폭을 추정한다.
"""
import math
import re

from .core import _detect_prefix

# 셀 좌우 안쪽 여백(합), 글자와 테두리 사이 숨 쉴 공간
_CELL_PAD = 1000
# 셀 상하 여백(합)
_CELL_VPAD = 566
# 한 줄이 차지하는 세로 배수(줄간격 포함 근사)
_LINE_FACTOR = 1.7
# 열이 무너지지 않을 최소 폭 (패딩 + 최소 글자 여유)
_MIN_COL = 1600


def _units(text):
    """텍스트의 시각적 폭(전각=1.0, 반각=0.55). 여러 줄이면 최장 줄 기준."""
    best = 0.0
    for line in text.split("\n"):
        u = sum(1.0 if ord(ch) > 0x2E7F else 0.55 for ch in line)
        best = max(best, u)
    return best


def _longest_token_units(text):
    """공백으로 못 쪼개지는 최장 토큰의 폭(줄바꿈으로도 못 줄이는 하한)."""
    best = 0.0
    for line in text.split("\n"):
        for tok in line.split():
            u = sum(1.0 if ord(ch) > 0x2E7F else 0.55 for ch in tok)
            best = max(best, u)
    return best


def _waterfill(demand, total):
    """표 전체 폭(total)을 유지하며 열폭을 배분한다.
    - 총 수요 <= total: 각 열이 제 수요를 받고, 남는 폭은 수요 비례로 분배
      (긴 내용 열이 더 많은 여유를 가져감).
    - 총 수요 > total: 워터필링 — 수요가 작은 열부터 제 수요를 온전히 채우고,
      큰 열들끼리 남은 폭을 균등히 나눈다. → 짧은 열이 굶어 무너지는 것을 방지."""
    n = len(demand)
    if n == 0:
        return []
    if sum(demand) <= total:
        extra = total - sum(demand)
        s = sum(demand) or 1.0
        return [d + extra * (d / s) for d in demand]
    out = [0.0] * n
    cols = set(range(n))
    remaining = float(total)
    while cols:
        share = remaining / len(cols)
        satisfied = [c for c in cols if demand[c] <= share]
        if not satisfied:                     # 남은 열 전부 share 초과 → 균등 분배
            for c in cols:
                out[c] = share
            break
        for c in satisfied:
            out[c] = demand[c]
            remaining -= demand[c]
            cols.discard(c)
    return out


def _cell_meta(doc, chunk, hp):
    """셀 chunk에서 colSpan/rowSpan/width/height/글꼴height 추출."""
    sp = re.search(r'<%s:cellSpan\b[^>]*\bcolSpan="(\d+)"[^>]*\browSpan="(\d+)"'
                   % hp, chunk)
    colspan = int(sp.group(1)) if sp else 1
    rowspan = int(sp.group(2)) if sp else 1
    sz = re.search(r'<%s:cellSz\b[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"'
                   % hp, chunk)
    width = int(sz.group(1)) if sz else None
    height = int(sz.group(2)) if sz else None
    font = doc._current_cell_font(chunk, hp)      # 1/100pt == 전각 폭(HWPUNIT)
    return colspan, rowspan, width, height, font


def autofit_table(doc, table_index, min_pt=6.0, allow_shrink=True):
    """표를 내용에 맞춰 자동 정렬한다. 반환:
       {"widths": [열폭...], "heights": {행:높이}, "shrunk": [(행,열)...]}"""
    tables = doc.tables()
    if not (0 <= table_index < len(tables)):
        raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
    tb = tables[table_index]
    if tb["nested"]:
        # 중첩 표는 폭 재분배가 위험 → 자동 맞춤 대상에서 제외
        raise ValueError("중첩 표는 autofit 대상이 아닙니다(수동 조정 필요).")
    sec = tb["sec"]
    xml = doc.files[sec].decode("utf-8")
    hp = _detect_prefix(xml, "tbl")
    ts, te = tb["span"]
    chunk = xml[ts:te]

    ncols = tb["cols"]
    # 표 전체 폭(유지 대상): 표 여는 태그 직후 첫 <hp:sz width>
    twm = re.search(r'<%s:sz\b[^>]*\bwidth="(\d+)"' % hp, chunk)
    # 셀 메타 수집
    metas = []          # (row, col, colspan, rowspan, width, height, font, text)
    for c in tb["cells"]:
        cs, ce = c["span"]
        colspan, rowspan, width, height, font = _cell_meta(
            doc, xml[cs:ce], hp)
        metas.append((c["row"], c["col"], colspan, rowspan,
                      width, height, font, c["text"]))

    # 표 전체 폭: 태그값 우선, 없으면 한 행(row 0)의 단일-열 셀 폭 합으로 추정
    if twm:
        total = int(twm.group(1))
    else:
        row0 = [m for m in metas if m[0] == 0 and m[4]]
        total = sum(m[4] for m in row0) or (_MIN_COL * ncols)

    # ---- 1) 열별 내용 폭 수요(demand) 계산 ----
    demand = [0.0] * ncols
    for (row, col, cspan, rspan, width, height, font, text) in metas:
        f = font or 1000
        need = _units(text) * f + _CELL_PAD          # 이 셀이 원하는 폭
        if cspan == 1:
            if 0 <= col < ncols:
                demand[col] = max(demand[col], need)
        else:
            # 병합 셀: 걸친 열들의 합이 need 이상이 되도록 나중에 보정
            pass
    demand = [max(d, _MIN_COL) for d in demand]

    # 병합 셀 보정: 걸친 열 폭 합이 부족하면 그 구간 최대 열에 부족분 가산
    for (row, col, cspan, rspan, width, height, font, text) in metas:
        if cspan <= 1:
            continue
        f = font or 1000
        need = _units(text) * f + _CELL_PAD
        seg = list(range(col, min(col + cspan, ncols)))
        if not seg:
            continue
        have = sum(demand[i] for i in seg)
        if have < need:
            widest = max(seg, key=lambda i: demand[i])
            demand[widest] += (need - have)

    # ---- 2) 표 전체 폭을 유지한 채 열폭 배분 (워터필링) ----
    overflow = sum(demand) > total   # 현재 글꼴로는 총폭 안에 다 못 들어감
    widths = [max(int(round(w)), 1) for w in _waterfill(demand, total)]
    # 반올림 오차를 가장 넓은 열에 흡수시켜 합 == total 보장
    diff = total - sum(widths)
    if widths:
        widths[widths.index(max(widths))] += diff
    doc.set_col_widths(table_index, widths)

    # 배분된 열폭 기준 각 열의 사용 가능 폭
    usable_col = [max(w - _CELL_PAD, 1) for w in widths]

    # ---- 3) 행 높이(줄바꿈 허용) + 4) 최후 글자 축소 ----
    heights = {}
    shrunk = []
    for (row, col, cspan, rspan, width, height, font, text) in metas:
        if rspan != 1:                # 세로 병합 행 높이는 건드리지 않음
            continue
        f = font or 1000
        seg = range(col, min(col + max(cspan, 1), ncols))
        avail = sum(usable_col[i] for i in seg) or usable_col[min(col, ncols - 1)]
        per_line = max(avail / f, 0.1)          # 한 줄에 들어갈 전각 글자 수
        u = _units(text)
        lines_wrap = max(len(text.split("\n")),
                         int(math.ceil(u / per_line)) if u else 1)
        need_h = int(lines_wrap * f * _LINE_FACTOR) + _CELL_VPAD
        if height and need_h > height:
            heights[row] = max(heights.get(row, 0), need_h)

        # 줄바꿈으로도 못 줄이는 긴 토큰이 열보다 넓으면 마지막 수단으로 축소
        if allow_shrink:
            tok = _longest_token_units(text)
            if tok * f > avail:
                try:
                    doc.fit_cell(table_index, row, col, min_pt=min_pt)
                    shrunk.append((row, col))
                except (ValueError, IndexError):
                    pass

    if heights:
        doc.set_row_heights(table_index, heights)

    # ---- 5) 구조 무결성 확인 (rowCnt/colCnt·병합) ----
    doc.verify(fix=True)

    return {"widths": widths, "heights": heights, "shrunk": shrunk,
            "total": total, "overflow": overflow}

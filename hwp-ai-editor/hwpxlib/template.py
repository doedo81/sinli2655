"""template — 표준 양식(템플릿) 준수 편집 (Phase B 핵심).

"표준 양식이 있으면 그걸 이해하고, 조건에 맞는 부분만 양식을 지키며 편집."

  extract_schema()  : 표를 분석해 양식 규칙(고정 칸 vs 채움 칸, 열 스타일,
                       반복 행 템플릿, 헤더 라벨→열)을 추출한다.
  apply_template()  : 데이터를 채움 칸에만 넣고(고정 칸·서식 불변), 데이터가
                       많으면 행을 자동 증설하고, AutoTable로 자동 맞춤한 뒤
                       양식/구조를 검증한다. 사람은 "무슨 데이터를 넣을지"만 준다.
  validate_template(): 고정 칸 불변·스타일 일관성·구조·규정을 점검한다.

저수준 XML은 손대지 않고, 검증된 HwpxDoc 메서드만 오케스트레이션한다.
"""
import re

from .core import GOV_DOC_RULES, _detect_prefix
from .autotable import autofit_table, _cell_meta


def extract_schema(doc, table_index):
    """표를 분석해 양식 스키마(dict)를 반환한다."""
    tables = doc.tables()
    if not (0 <= table_index < len(tables)):
        raise IndexError("표 번호는 0~%d 사이여야 합니다." % (len(tables) - 1))
    tb = tables[table_index]
    xml = doc.files[tb["sec"]].decode("utf-8")
    hp = _detect_prefix(xml, "tbl")
    nrows, ncols = tb["rows"], tb["cols"]

    cellmap = {}
    for c in tb["cells"]:
        r, col = c["row"], c["col"]
        cs, ce = c["span"]
        colspan, rowspan, width, height, font = _cell_meta(doc, xml[cs:ce], hp)
        cellmap[(r, col)] = {"text": c["text"], "colspan": colspan,
                             "rowspan": rowspan, "width": width}

    def row_cols(r):
        return [col for (rr, col) in cellmap if rr == r]

    def nonempty(r, col):
        return bool(cellmap.get((r, col), {}).get("text", "").strip())

    # 헤더 행: 맨 앞에서부터, 존재하는 셀이 모두 비어있지 않은 행들
    header_rows = []
    for r in range(nrows):
        cols = row_cols(r)
        if cols and all(nonempty(r, col) for col in cols):
            header_rows.append(r)
        else:
            break
    body_rows = [r for r in range(nrows) if r not in header_rows]

    # 라벨 열: 본문 모든 행에서 채워져 있고, 그 행들에 빈 칸(값 자리)이 있는 열
    label_cols = []
    for col in range(ncols):
        if body_rows and all((r, col) in cellmap and nonempty(r, col)
                             for r in body_rows):
            other_empty = any((r, cc) in cellmap and not nonempty(r, cc)
                              for r in body_rows for cc in range(ncols)
                              if cc != col)
            if other_empty:
                label_cols.append(col)

    # 고정 칸 vs 채움 칸
    fixed, fillable = [], []
    for (r, col) in cellmap:
        if r in header_rows or col in label_cols:
            fixed.append((r, col))
        else:
            fillable.append((r, col))
    fixed.sort()
    fillable.sort()
    fill_cols = sorted({col for (r, col) in fillable})
    data_rows = sorted({r for (r, col) in fillable})

    # 반복 행 템플릿: 마지막 데이터 행 중 rowSpan>1이 없는 행(copy_row 제약)
    repeat_row = None
    for r in reversed(data_rows):
        if all(cellmap[(r, col)]["rowspan"] == 1
               for col in row_cols(r) if (r, col) in cellmap):
            repeat_row = r
            break

    # 헤더 라벨 → 열 매핑 (본문에 가장 가까운 헤더 행 기준)
    label_to_col = {}
    if header_rows:
        hr = header_rows[-1]
        for col in range(ncols):
            t = cellmap.get((hr, col), {}).get("text", "").strip()
            if t:
                label_to_col[t] = col

    # 열별 대표 스타일 + 대표 셀 좌표
    col_style, col_ref = {}, {}
    for col in fill_cols:
        if data_rows and (data_rows[0], col) in cellmap:
            r0 = data_rows[0]
            st = doc.cell_style(table_index, r0, col)
            col_style[col] = {"font": st["font"], "size": st["size"],
                              "align": st["align"]}
            col_ref[col] = (r0, col)

    fixed_text = {(r, col): cellmap[(r, col)]["text"] for (r, col) in fixed}
    border = doc.table_style(table_index).get("borderFill")

    return {
        "cols": ncols, "rows": nrows,
        "header_rows": header_rows, "label_cols": label_cols,
        "fixed": fixed, "fillable": set(fillable),
        "fill_cols": fill_cols, "data_rows": data_rows,
        "repeat_row": repeat_row, "label_to_col": label_to_col,
        "col_style": col_style, "col_ref": col_ref,
        "fixed_text": fixed_text, "border_fill": border,
        "rules": GOV_DOC_RULES,
    }


def _record_items(rec, schema):
    """레코드(dict 또는 list)를 [(열, 값)...] 로 정규화."""
    if isinstance(rec, dict):
        out = []
        for label, val in rec.items():
            col = schema["label_to_col"].get(label)
            if col is not None:
                out.append((col, val))
        return out
    return [(schema["fill_cols"][j], v)
            for j, v in enumerate(rec) if j < len(schema["fill_cols"])]


def apply_template(doc, table_index, records, schema=None,
                   autofit=True, enforce_style=True):
    """데이터(records)를 양식의 채움 칸에만 넣는다. 반환:
       {"added_rows", "filled", "autofit", "issues"}"""
    if schema is None:
        schema = extract_schema(doc, table_index)
    records = list(records)
    data_rows = list(schema["data_rows"])
    need, have = len(records), len(data_rows)

    added = 0
    if need > have:
        if schema["repeat_row"] is None:
            raise ValueError("이 양식은 행 자동 증설이 불가합니다(병합 행). "
                             "수동으로 행을 추가하세요.")
        added = need - have
        doc.copy_row(table_index, schema["repeat_row"], added)
        schema = extract_schema(doc, table_index)     # 위치 갱신
        data_rows = list(schema["data_rows"])

    filled = 0
    for i, rec in enumerate(records):
        if i >= len(data_rows):
            break
        r = data_rows[i]
        for col, val in _record_items(rec, schema):
            if (r, col) not in schema["fillable"]:
                continue                              # 고정 칸은 절대 안 건드림
            doc.set_cell(table_index, r, col,
                         "" if val is None else str(val))
            filled += 1
            if enforce_style and col in schema["col_ref"]:
                rr, rc = schema["col_ref"][col]
                ref = schema["col_style"].get(col)
                if ref and (rr, rc) != (r, col):
                    cur = doc.cell_style(table_index, r, col)
                    if (cur["font"], cur["size"], cur["align"]) != \
                       (ref["font"], ref["size"], ref["align"]):
                        try:
                            doc.copy_style(table_index, r, col, rr, rc)
                        except (ValueError, IndexError):
                            pass

    # 데이터가 표보다 적으면 남는 데이터 행의 채움 칸을 비운다
    if need < have:
        for r in data_rows[need:]:
            for (rr, col) in schema["fillable"]:
                if rr == r:
                    try:
                        doc.set_cell(table_index, r, col, "")
                    except (ValueError, IndexError):
                        pass

    rep = {"added_rows": added, "filled": filled, "autofit": None}
    if autofit:
        try:
            rep["autofit"] = autofit_table(doc, table_index)
        except ValueError:
            rep["autofit"] = None                     # 중첩표 등 예외 케이스
    rep["issues"] = validate_template(doc, table_index, schema)
    return rep


def validate_template(doc, table_index, schema):
    """고정 칸 불변·스타일 일관성·구조·규정을 점검해 문제 목록을 반환."""
    issues = []
    tb = doc.tables()[table_index]
    cur = {(c["row"], c["col"]): c["text"] for c in tb["cells"]}

    # 고정 칸 텍스트 불변
    for (r, col), t in schema["fixed_text"].items():
        if cur.get((r, col), "") != t:
            issues.append({"kind": "고정칸 변경", "cell": (r, col),
                           "detail": "'%s' → '%s'" % (t, cur.get((r, col), ""))})

    # 글꼴·정렬 일관성
    ct = doc.check_table(table_index)
    for (df, ds, da), cells in ct.get("deviations", []):
        issues.append({"kind": "스타일 이탈",
                       "detail": "%s %.1fpt %s (%d칸)" % (df, ds, da, len(cells))})

    # 구조 무결성
    vissues, _ = doc.verify()
    for it in vissues:
        if it["table"] == table_index:
            issues.append({"kind": it["kind"], "detail": it["detail"]})

    # 공문서 날짜 표기 권고 (연월일 → '2026. 3. 1.')
    for (r, col), t in cur.items():
        if re.search(r"\d{4}\s*년\s*\d{1,2}\s*월", t):
            issues.append({"kind": "날짜표기 권고", "cell": (r, col),
                           "detail": "'연월일' 대신 '2026. 3. 1.' 형식 권장"})

    return issues

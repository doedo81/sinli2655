"""ops — 편집 op 실행기 + 조회/검증 헬퍼 (수동 UI와 AI 에이전트가 공유).

app.py(수동 편집)와 ai_agent.py(자연어 편집)가 동일한 코드 경로로 문서를
편집하도록, 저수준 실행을 여기 한 곳에 모은다. 저수준 XML은 검증된 HwpxDoc
엔진이 처리하며, 각 op은 그 메서드에 1:1 매핑된다.
"""
import re

from hwpxlib import HwpxDoc, autofit_table, apply_template  # noqa: F401


def tables_summary(doc):
    return [{"index": t["index"], "rows": t["rows"], "cols": t["cols"],
             "nested": t["nested"]} for t in doc.tables()]


def table_detail(doc, i):
    tbs = doc.tables()
    if not (0 <= i < len(tbs)):
        return None
    t = tbs[i]
    cells = [{"row": c["row"], "col": c["col"], "text": c["text"]}
             for c in t["cells"]]
    return {"index": i, "rows": t["rows"], "cols": t["cols"], "cells": cells}


def verify_issues(doc):
    issues, _ = doc.verify()
    return issues


def _first_int(s):
    m = re.search(r"-?\d+", s or "")
    return int(m.group(0)) if m else 0


def _table_index_by_id(doc, table_id):
    """방금 만든 표의 index를 tbl id로 찾는다(중간 삽입도 정확).
    span 시작부의 <...:tbl id="N" ...>에서 id를 읽어 대조. 못 찾으면 마지막."""
    tables = doc.tables()
    for t in tables:
        xml = doc.files[t["sec"]].decode("utf-8")
        s, e = t["span"]
        m = re.search(r'<\w+:tbl\b[^>]*\bid="(\d+)"', xml[s:min(e, s + 300)])
        if m and int(m.group(1)) == int(table_id):
            return t["index"]
    return len(tables) - 1


def sum_row(doc, ti, row, sum_col, cols=None):
    """행의 데이터 칸 숫자를 더해 합계 칸에 넣는다.
    cols 미지정 시 0열(라벨)과 sum_col을 제외한 그 행의 모든 칸을 더한다."""
    t = doc.tables()[ti]
    rowcells = {c["col"]: c["text"] for c in t["cells"] if c["row"] == row}
    if cols is None:
        cols = [c for c in rowcells if c != 0 and c != sum_col]
    total = sum(_first_int(rowcells.get(c, "0")) for c in cols)
    doc.set_cell(ti, row, sum_col, str(total))
    return total


def do_op(doc, op, args):
    """편집 op 실행. 반환: 부가정보 dict(없으면 {})."""
    if op == "set_cell":
        doc.set_cell(int(args["ti"]), int(args["row"]), int(args["col"]),
                     str(args.get("text", "")))
    elif op == "autofit":
        return {"autofit": autofit_table(doc, int(args["ti"]))}
    elif op == "del_col":
        doc.del_col(int(args["ti"]), int(args["col"]))
    elif op == "del_row":
        doc.del_row(int(args["ti"]), int(args["row"]))
    elif op == "del_table":
        doc.del_table(int(args["ti"]))
    elif op == "copy_row":
        doc.copy_row(int(args["ti"]), int(args["row"]),
                     int(args.get("count", 1)))
    elif op == "replace_regex":
        n = doc.replace_regex(args["pattern"], args["repl"])
        return {"count": n}
    elif op == "apply_template":
        rep = apply_template(doc, int(args["ti"]), args["records"])
        return {"report": {k: rep[k] for k in ("added_rows", "filled")}}
    elif op == "add_table":
        style = {}
        if args.get("style_from") is not None:
            st = doc.table_style(int(args["style_from"]))
            style = {"char_pr": st["charPr"], "para_pr": st["paraPr"],
                     "border_fill": st["borderFill"]}
        after = args.get("after_paragraph")
        info = doc.add_table(int(args["rows"]), int(args["cols"]),
                             data=args.get("data"),
                             after_paragraph=(None if after is None else int(after)),
                             **style)
        new_ti = _table_index_by_id(doc, info["table_id"])
        autofit_table(doc, new_ti)
        return {"new_table": new_ti, "rows": info["rows"], "cols": info["cols"]}
    elif op == "add_paragraph":
        doc.add_paragraph(str(args.get("text", "")))
    elif op == "sum_row":
        total = sum_row(doc, int(args["ti"]), int(args["row"]),
                        int(args["sum_col"]), args.get("cols"))
        return {"total": total}
    else:
        raise ValueError("알 수 없는 op: %s" % op)
    return {}

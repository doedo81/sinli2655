#!/usr/bin/env python3
"""hwpxlib 웹앱 백엔드 — Python 표준 라이브러리만 사용(무외부의존).

실행:  python3 -m server.app   →  http://localhost:8000

브라우저에서 .hwpx를 올리고, 표를 보고 편집하고(셀 수정·autofit·행/열 삭제·
정규식 치환·합계 재계산), 다운로드한다. 저수준 편집은 검증된 HwpxDoc 엔진이
그대로 처리하며, 매 편집 후 verify 결과를 함께 돌려준다.
"""
import io
import json
import os
import re
import base64
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from hwpxlib import HwpxDoc, autofit_table, apply_template

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "web")

# 세션별 문서 (로컬 단일 프로세스용 인메모리 저장소)
SESSIONS = {}


# ---------------------------------------------------------------- 유틸
def _tables_summary(doc):
    return [{"index": t["index"], "rows": t["rows"], "cols": t["cols"],
             "nested": t["nested"]} for t in doc.tables()]


def _table_detail(doc, i):
    tbs = doc.tables()
    if not (0 <= i < len(tbs)):
        return None
    t = tbs[i]
    cells = [{"row": c["row"], "col": c["col"], "text": c["text"]}
             for c in t["cells"]]
    return {"index": i, "rows": t["rows"], "cols": t["cols"], "cells": cells}


def _verify(doc):
    issues, _ = doc.verify()
    return issues


def _first_int(s):
    m = re.search(r"-?\d+", s or "")
    return int(m.group(0)) if m else 0


def _sum_row(doc, ti, row, sum_col, cols=None):
    """행의 데이터 칸 숫자를 더해 합계 칸에 넣는다(요청 실작업의 일반화).
    cols 미지정 시 0열(라벨)과 sum_col을 제외한 그 행의 모든 칸을 더한다."""
    t = doc.tables()[ti]
    rowcells = {c["col"]: c["text"] for c in t["cells"] if c["row"] == row}
    if cols is None:
        cols = [c for c in rowcells if c != 0 and c != sum_col]
    total = sum(_first_int(rowcells.get(c, "0")) for c in cols)
    doc.set_cell(ti, row, sum_col, str(total))
    return total


# ---------------------------------------------------------------- op 처리
def _do_op(doc, op, args):
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
    elif op == "sum_row":
        total = _sum_row(doc, int(args["ti"]), int(args["row"]),
                         int(args["sum_col"]), args.get("cols"))
        return {"total": total}
    else:
        raise ValueError("알 수 없는 op: %s" % op)
    return {}


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self._send(code, {"ok": False, "error": msg})

    def _doc(self, qs):
        sid = (qs.get("session", [None])[0])
        return SESSIONS.get(sid), sid

    def _body_json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def log_message(self, *a):
        pass  # 조용히

    # ---------- GET ----------
    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            return self._file("index.html", "text/html; charset=utf-8")
        if u.path.startswith("/web/"):
            return self._file(u.path[len("/web/"):], self._ctype(u.path))
        if u.path == "/api/table":
            doc, _ = self._doc(qs)
            if not doc:
                return self._err(404, "세션 없음")
            d = _table_detail(doc, int(qs.get("i", ["0"])[0]))
            return self._send(200, d or {"error": "표 없음"})
        if u.path == "/api/paragraphs":
            doc, _ = self._doc(qs)
            if not doc:
                return self._err(404, "세션 없음")
            ps = [{"i": i, "text": t} for _, _, i, t in doc.paragraphs()]
            return self._send(200, ps)
        if u.path == "/api/download":
            doc, _ = self._doc(qs)
            if not doc:
                return self._err(404, "세션 없음")
            data = doc.save_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/haansofthwp")
            self.send_header("Content-Disposition",
                             'attachment; filename="edited.hwpx"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        return self._err(404, "not found")

    # ---------- POST ----------
    def do_POST(self):
        u = urlparse(self.path)
        try:
            if u.path == "/api/upload":
                body = self._body_json()
                data = base64.b64decode(body["b64"])
                doc = HwpxDoc.from_bytes(data)
                sid = uuid.uuid4().hex
                SESSIONS[sid] = doc
                return self._send(200, {
                    "ok": True, "session": sid,
                    "name": body.get("name", "문서.hwpx"),
                    "tables": _tables_summary(doc),
                    "paras": len(doc.paragraphs()),
                    "verify": _verify(doc)})
            if u.path == "/api/op":
                body = self._body_json()
                doc = SESSIONS.get(body.get("session"))
                if not doc:
                    return self._err(404, "세션 없음")
                extra = _do_op(doc, body["op"], body.get("args", {}))
                out = {"ok": True, "verify": _verify(doc),
                       "tables": _tables_summary(doc)}
                out.update(extra)
                ti = body.get("args", {}).get("ti")
                if ti is not None:
                    d = _table_detail(doc, int(ti))
                    if d:
                        out["table"] = d
                return self._send(200, out)
        except Exception as e:  # 편집 실패는 사용자에게 그대로 전달
            return self._err(400, "%s: %s" % (type(e).__name__, e))
        return self._err(404, "not found")

    # ---------- 정적 ----------
    def _ctype(self, path):
        if path.endswith(".html"):
            return "text/html; charset=utf-8"
        if path.endswith(".js"):
            return "text/javascript; charset=utf-8"
        if path.endswith(".css"):
            return "text/css; charset=utf-8"
        return "application/octet-stream"

    def _file(self, rel, ctype):
        path = os.path.normpath(os.path.join(WEB_DIR, rel))
        if not path.startswith(WEB_DIR) or not os.path.isfile(path):
            return self._err(404, "파일 없음")
        with open(path, "rb") as f:
            return self._send(200, f.read(), ctype)


def main(port=8000):
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("한글 편집기 웹앱 → http://localhost:%d  (Ctrl+C 종료)" % port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n종료")


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)

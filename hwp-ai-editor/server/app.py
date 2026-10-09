#!/usr/bin/env python3
"""hwpxlib 웹앱 백엔드 — Python 표준 라이브러리만 사용(무외부의존).

실행:  python3 -m server.app   →  http://localhost:8000

브라우저에서 .hwpx를 올리고, 표를 보고 편집하고(셀 수정·autofit·행/열 삭제·
정규식 치환·합계 재계산), 다운로드한다. 저수준 편집은 검증된 HwpxDoc 엔진이
그대로 처리하며, 매 편집 후 verify 결과를 함께 돌려준다.
"""
import json
import os
import base64
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from hwpxlib import HwpxDoc
from hwpxlib.hwp_reader import read_hwp_text, is_hwp
from server import ops
from server.ai_agent import run_agent, answer_about_text

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "web")

# 세션별 문서 (로컬 단일 프로세스용 인메모리 저장소)
SESSIONS = {}
# 세션별 실행취소 스냅샷(직전 문서 바이트). AI 편집 전에 저장.
UNDO = {}
# 구형 .hwp 읽기전용 세션: sid → 추출 텍스트(질의응답용, 편집 불가)
HWP_TEXT = {}


def _context_text(sid):
    """질의응답용 컨텍스트 텍스트를 세션 종류에 맞게 만든다."""
    doc = SESSIONS.get(sid)
    if doc is not None:
        dt = ops.document_text(doc)
        lines = [p["text"] for p in dt["paragraphs"]]
        for tb in dt["tables"]:
            lines.append("[표 %d]" % tb["index"])
            for row in tb["grid"]:
                lines.append(" | ".join(row))
        return "\n".join(lines)
    return HWP_TEXT.get(sid)


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
            d = ops.table_detail(doc, int(qs.get("i", ["0"])[0]))
            return self._send(200, d or {"error": "표 없음"})
        if u.path == "/api/review":
            doc, _ = self._doc(qs)
            if not doc:
                return self._err(404, "세션 없음")
            return self._send(200, {"ok": True,
                                    "issues": ops.review_compliance(doc)})
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
                # 구형 .hwp: 읽기 전용(문단 텍스트만). 편집은 .hwpx 변환 경유.
                if is_hwp(data):
                    try:
                        r = read_hwp_text(data)
                    except RuntimeError as e:
                        return self._err(400, str(e))
                    # 읽기전용 세션 발급 → 요약·질의응답(/api/ask) 지원
                    sid = uuid.uuid4().hex
                    HWP_TEXT[sid] = "\n".join(r["paragraphs"])
                    return self._send(200, {
                        "ok": True, "kind": "hwp", "session": sid,
                        "name": body.get("name", "문서.hwp"),
                        "paragraphs": r["paragraphs"],
                        "sections": r["sections"],
                        "note": r.get("note",
                            "구형 .hwp는 읽기 전용입니다(분석·요약용). "
                            "편집하려면 한/글에서 .hwpx로 저장 후 업로드하세요.")})
                doc = HwpxDoc.from_bytes(data)
                sid = uuid.uuid4().hex
                SESSIONS[sid] = doc
                UNDO.pop(sid, None)
                return self._send(200, {
                    "ok": True, "kind": "hwpx", "session": sid,
                    "name": body.get("name", "문서.hwpx"),
                    "tables": ops.tables_summary(doc),
                    "paras": len(doc.paragraphs()),
                    "verify": ops.verify_issues(doc)})
            if u.path == "/api/op":
                body = self._body_json()
                sid = body.get("session")
                doc = SESSIONS.get(sid)
                if not doc:
                    return self._err(404, "세션 없음")
                UNDO[sid] = doc.save_bytes()  # 실행취소용 스냅샷
                extra = ops.do_op(doc, body["op"], body.get("args", {}))
                out = {"ok": True, "verify": ops.verify_issues(doc),
                       "tables": ops.tables_summary(doc)}
                out.update(extra)
                ti = body.get("args", {}).get("ti")
                if ti is not None:
                    d = ops.table_detail(doc, int(ti))
                    if d:
                        out["table"] = d
                return self._send(200, out)
            if u.path == "/api/new":
                doc = HwpxDoc.new()
                sid = uuid.uuid4().hex
                SESSIONS[sid] = doc
                UNDO.pop(sid, None)
                return self._send(200, {
                    "ok": True, "kind": "hwpx", "session": sid,
                    "name": "새 문서.hwpx",
                    "tables": ops.tables_summary(doc),
                    "paras": len(doc.paragraphs()),
                    "verify": ops.verify_issues(doc)})
            if u.path == "/api/chat":
                return self._chat()
            if u.path == "/api/undo":
                return self._undo()
            if u.path == "/api/ask":
                return self._ask()
        except Exception as e:  # 편집 실패는 사용자에게 그대로 전달
            return self._err(400, "%s: %s" % (type(e).__name__, e))
        return self._err(404, "not found")

    # ---------- AI 채팅 / 실행취소 ----------
    def _chat(self):
        body = self._body_json()
        sid = body.get("session")
        doc = SESSIONS.get(sid)
        if not doc:
            return self._err(404, "세션 없음")
        api_key = body.get("api_key") or ""
        if not api_key:
            return self._err(400, "Claude API 키가 필요합니다.")
        msg = body.get("message", "")
        model = body.get("model") or "claude-opus-4-8"
        UNDO[sid] = doc.save_bytes()  # AI 편집 전 스냅샷(실행취소용)
        try:
            res = run_agent(doc, msg, api_key, model=model)
        except Exception as e:
            # 실패 시 스냅샷 복원(부분편집 방지)
            try:
                SESSIONS[sid] = HwpxDoc.from_bytes(UNDO[sid])
            except Exception:
                pass
            return self._err(400, "%s: %s" % (type(e).__name__, e))
        out = {"ok": True, "reply": res["reply"], "actions": res["actions"],
               "verify": res["verify"], "tables": ops.tables_summary(doc)}
        return self._send(200, out)

    def _undo(self):
        body = self._body_json()
        sid = body.get("session")
        snap = UNDO.get(sid)
        if snap is None:
            return self._err(400, "되돌릴 편집이 없습니다.")
        doc = HwpxDoc.from_bytes(snap)
        SESSIONS[sid] = doc
        del UNDO[sid]
        return self._send(200, {"ok": True, "verify": ops.verify_issues(doc),
                                "tables": ops.tables_summary(doc)})

    def _ask(self):
        """요약·분석·질의응답 (읽기 전용). .hwpx·.hwp 모두 지원."""
        body = self._body_json()
        sid = body.get("session")
        text = _context_text(sid)
        if text is None:
            return self._err(404, "세션 없음")
        api_key = body.get("api_key") or ""
        if not api_key:
            return self._err(400, "Claude API 키가 필요합니다.")
        model = body.get("model") or "claude-opus-4-8"
        res = answer_about_text(text, body.get("message", ""), api_key, model=model)
        return self._send(200, {"ok": True, "reply": res["reply"]})

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

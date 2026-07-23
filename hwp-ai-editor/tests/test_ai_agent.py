"""ai_agent 단위 테스트 (Phase C).

Messages API 호출 함수를 목(mock)으로 교체해, 실제 Claude 키 없이
tool-use 루프가 엔진 op을 실행하고 상태를 바꾸는지 검증한다.
python3 tests/test_ai_agent.py
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import HwpxDoc                       # noqa: E402
from server.ai_agent import run_agent, answer_about_text   # noqa: E402
from tests.fixtures import make_sample_hwpx        # noqa: E402


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print("  ok:", msg)


def _text(t):
    return {"type": "text", "text": t}


def _tool_use(uid, name, inp):
    return {"type": "tool_use", "id": uid, "name": name, "input": inp}


class MockClaude:
    """미리 정한 응답 대본(scripted)을 순서대로 돌려주는 Messages API 목.

    각 응답은 (stop_reason, content_blocks). run_agent가 보내는 payload를
    calls에 기록해 tools/messages 전달을 확인할 수 있다.
    """
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.calls = []

    def __call__(self, api_key, model, payload, base_url=None):
        # 실제 HTTP는 매 호출 JSON 직렬화(스냅샷)하므로 목도 복사본을 기록
        self.calls.append(copy.deepcopy(payload))
        stop, content = self.scripted.pop(0)
        return {"stop_reason": stop, "content": content, "model": model}


def test_single_edit():
    print("[test] tool_use(set_cell) → tool_result → end_turn")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    mock = MockClaude([
        ("tool_use", [_tool_use("t1", "set_cell",
                                {"ti": 0, "row": 1, "col": 0, "text": "김철수"})]),
        ("end_turn", [_text("1행 0열을 '김철수'로 바꿨습니다.")]),
    ])
    res = run_agent(doc, "현황표 첫 행 성명을 김철수로", "sk-fake",
                    call=mock)
    cell = next(c for c in doc.tables()[0]["cells"]
                if c["row"] == 1 and c["col"] == 0)
    _assert(cell["text"] == "김철수", "엔진 셀이 실제로 편집됨")
    _assert(len(res["actions"]) == 1 and res["actions"][0]["tool"] == "set_cell",
            "actions에 set_cell 기록")
    _assert("김철수" in res["reply"], "최종 reply 텍스트 반환")
    _assert(len(mock.calls) == 2, "두 번 왕복(도구 실행 후 재호출)")
    _assert(mock.calls[0]["messages"][0]["content"].startswith("현황표"),
            "첫 메시지에 사용자 지시 전달")


def test_read_then_edit():
    print("[test] 조회(get_table) 후 편집 — 조회는 actions에 안 남음")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    mock = MockClaude([
        ("tool_use", [_tool_use("r1", "get_table", {"ti": 0})]),
        ("tool_use", [_tool_use("e1", "set_cell",
                                {"ti": 0, "row": 1, "col": 2, "text": "완료"})]),
        ("end_turn", [_text("확인 후 2열을 완료로 채웠습니다.")]),
    ])
    res = run_agent(doc, "내용 확인하고 비고를 완료로", "sk-fake", call=mock)
    _assert(len(res["actions"]) == 1, "조회는 제외, 편집만 actions에 1건")
    cell = next(c for c in doc.tables()[0]["cells"]
                if c["row"] == 1 and c["col"] == 2)
    _assert(cell["text"] == "완료", "편집 반영")
    # tool_result가 user 턴으로 되돌아갔는지(assistant/user 교대)
    roles = [m["role"] for m in mock.calls[-1]["messages"]]
    _assert(roles.count("assistant") >= 2, "assistant content가 히스토리에 보존")


def test_tool_error_recovers():
    print("[test] 잘못된 도구 인자 → is_error tool_result → 모델 재시도")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    mock = MockClaude([
        # 없는 표 번호 → do_op에서 예외 → is_error 결과
        ("tool_use", [_tool_use("b1", "set_cell",
                                {"ti": 99, "row": 0, "col": 0, "text": "x"})]),
        # 모델이 바로잡아 올바른 표로 재시도
        ("tool_use", [_tool_use("b2", "set_cell",
                                {"ti": 0, "row": 0, "col": 0, "text": "성명2"})]),
        ("end_turn", [_text("올바른 표로 수정했습니다.")]),
    ])
    res = run_agent(doc, "편집", "sk-fake", call=mock)
    # 마지막 user 턴(재시도 요청)에 is_error 결과가 들어갔는지
    err_turn = mock.calls[1]["messages"][-1]["content"]
    _assert(any(b.get("is_error") for b in err_turn), "실패는 is_error로 전달")
    _assert(len(res["actions"]) == 1, "성공한 편집만 actions에 기록")
    cell = next(c for c in doc.tables()[0]["cells"]
                if c["row"] == 0 and c["col"] == 0)
    _assert(cell["text"] == "성명2", "재시도 편집 반영")


def test_generate_table():
    print("[test] add_table 생성 → new_table 번호로 채우기 → end_turn")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    before = len(doc.tables())
    mock = MockClaude([
        ("tool_use", [_tool_use("g1", "add_table",
                                {"rows": 2, "cols": 3,
                                 "data": [["교과", "시수", "비고"], ["국어", "20", ""]]})]),
        # 생성된 표(index=before)에 셀 하나 더 채움
        ("tool_use", [_tool_use("g2", "set_cell",
                                {"ti": before, "row": 1, "col": 2, "text": "확정"})]),
        ("end_turn", [_text("과목별 시수 표를 만들었습니다.")]),
    ])
    res = run_agent(doc, "과목별 시수 표 만들어줘", "sk-fake", call=mock)
    tbs = doc.tables()
    _assert(len(tbs) == before + 1, "표 개수 %d→%d로 증가" % (before, len(tbs)))
    cells = {(c["row"], c["col"]): c["text"] for c in tbs[before]["cells"]}
    _assert(cells.get((0, 0)) == "교과" and cells.get((1, 1)) == "20",
            "add_table data가 새 표에 채워짐")
    _assert(cells.get((1, 2)) == "확정", "생성 후 set_cell로 새 표 편집됨")
    tools_used = [a["tool"] for a in res["actions"]]
    _assert("add_table" in tools_used and "set_cell" in tools_used,
            "actions에 add_table·set_cell 기록")
    _assert(res["verify"] == [], "생성 후 verify 이상 없음")
    # 저장→재로딩 무결
    doc2 = HwpxDoc.from_bytes(doc.save_bytes())
    _assert(len(doc2.tables()) == before + 1, "저장→재로딩 후 표 수 유지")


def test_generate_paragraph():
    print("[test] add_paragraph 생성 → 문단 수 증가")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    before = len(doc.paragraphs())
    mock = MockClaude([
        ("tool_use", [_tool_use("p1", "add_paragraph",
                                {"text": "붙임. 세부 계획 1부."})]),
        ("end_turn", [_text("본문 문단을 추가했습니다.")]),
    ])
    res = run_agent(doc, "붙임 문구 추가해줘", "sk-fake", call=mock)
    paras = doc.paragraphs()
    _assert(len(paras) == before + 1, "문단 수 %d→%d로 증가" % (before, len(paras)))
    _assert(any("붙임. 세부 계획 1부." in t for _, _, _, t in paras),
            "추가 문단 텍스트 반영")
    _assert(res["actions"][0]["tool"] == "add_paragraph", "actions에 add_paragraph")


def test_no_tool_immediate_reply():
    print("[test] 도구 없이 바로 답변(질의)")
    doc = HwpxDoc.from_bytes(make_sample_hwpx())
    mock = MockClaude([
        ("end_turn", [_text("이 문서에는 표가 1개 있습니다.")]),
    ])
    res = run_agent(doc, "표가 몇 개야?", "sk-fake", call=mock)
    _assert(res["actions"] == [], "편집 없음")
    _assert("표" in res["reply"], "답변 텍스트 반환")
    _assert(len(mock.calls) == 1, "한 번만 호출")


def test_review_compliance_tool():
    print("[test] review_compliance 도구 → 위반 목록 tool_result")
    doc = HwpxDoc.from_bytes(make_sample_hwpx([
        ["일시", "2026년 3월 1일 오후 2시"],
    ]))
    mock = MockClaude([
        ("tool_use", [_tool_use("r1", "review_compliance", {})]),
        ("end_turn", [_text("날짜·시각 표기 2건을 권고합니다.")]),
    ])
    res = run_agent(doc, "규정 검토해줘", "sk-fake", call=mock)
    # 도구 결과(issues)가 모델에게 tool_result로 전달됐는지
    tr = mock.calls[1]["messages"][-1]["content"][0]
    payload = json.loads(tr["content"])
    kinds = [i["kind"] for i in payload["issues"]]
    _assert("날짜표기" in kinds and "시각표기" in kinds,
            "규정 위반이 tool_result로 전달")
    _assert(res["actions"] == [], "조회 도구라 편집 actions 없음")


def test_get_document_text_tool():
    print("[test] get_document_text 도구 → 전체 텍스트 tool_result")
    doc = HwpxDoc.from_bytes(make_sample_hwpx([["성명", "부서"], ["홍길동", "기획과"]]))
    mock = MockClaude([
        ("tool_use", [_tool_use("d1", "get_document_text", {})]),
        ("end_turn", [_text("성명·부서 2열 표가 있는 문서입니다.")]),
    ])
    run_agent(doc, "이 문서 요약해줘", "sk-fake", call=mock)
    tr = mock.calls[1]["messages"][-1]["content"][0]
    payload = json.loads(tr["content"])
    _assert("tables" in payload and payload["tables"][0]["grid"][1] == ["홍길동", "기획과"],
            "전체 문서 텍스트(표 격자 포함)가 도구 결과로 전달")


def test_answer_about_text():
    print("[test] answer_about_text 단일 호출(도구 없음, 편집 없음)")
    calls = []

    def fake(api_key, model, payload, base_url=None):
        calls.append(payload)
        return {"stop_reason": "end_turn", "model": model,
                "content": [{"type": "text", "text": "이 문서는 5학년 교육과정입니다."}]}
    res = answer_about_text("5학년 교육과정 운영 계획 ...", "몇 학년이야?",
                            "sk-fake", call=fake)
    _assert("5학년" in res["reply"], "문서 컨텍스트 기반 답변 반환")
    _assert(len(calls) == 1 and "tools" not in calls[0],
            "도구 없는 단일 호출")
    _assert("몇 학년" in calls[0]["messages"][0]["content"],
            "질문이 프롬프트에 포함")


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 ai_agent 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

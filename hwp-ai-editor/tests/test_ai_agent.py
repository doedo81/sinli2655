"""ai_agent 단위 테스트 (Phase C).

Messages API 호출 함수를 목(mock)으로 교체해, 실제 Claude 키 없이
tool-use 루프가 엔진 op을 실행하고 상태를 바꾸는지 검증한다.
python3 tests/test_ai_agent.py
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hwpxlib import HwpxDoc                       # noqa: E402
from server.ai_agent import run_agent              # noqa: E402
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


def run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print("\n모든 ai_agent 테스트 통과 (%d개)" % len(fns))


if __name__ == "__main__":
    run_all()

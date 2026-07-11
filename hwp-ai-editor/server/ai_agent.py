"""ai_agent — Claude tool-use 자연어 편집 에이전트.

사용자의 자연어 지시("3번 표 모든 과목 20으로", "담임 열 삭제")를 받아
Claude가 도구(엔진 op)를 골라 실행하고 verify로 자기검증한 뒤 결과를 보고한다.

무외부의존 철학을 지켜 anthropic SDK 대신 표준 라이브러리 urllib로 Messages
API를 직접 호출한다. HTTP 호출은 `_call_messages` 한 함수로 격리해 테스트에서
목(mock)으로 교체할 수 있게 했다(실제 키 없이 로직 검증 가능).

**API 키는 서버에 저장·로깅하지 않는다** — 요청 처리 중에만 인자로 흐른다.
"""
import json
import urllib.request
import urllib.error

from hwpxlib import GOV_DOC_RULES
from server import ops
from server.tools import TOOLS, EDIT_TOOL_NAMES

_MAX_TURNS = 12  # tool-use 왕복 상한(무한루프 방지)

_SYSTEM = (
    "당신은 한글(HWPX) 문서 편집기의 AI 에이전트입니다. 사용자의 자연어 지시를 "
    "받아 제공된 도구로 문서를 편집합니다.\n"
    "원칙:\n"
    "1. 편집 전에 먼저 list_tables/get_table/list_paragraphs로 현재 상태를 "
    "확인하세요. 표 번호·행·열은 반드시 조회로 확인한 값을 쓰고 추측하지 마세요.\n"
    "2. 행·열·치수는 사용자가 지정하지 않습니다. 당신이 내용에 맞게 계산하세요. "
    "셀을 채우거나 편집한 뒤에는 autofit으로 표 레이아웃을 정리하세요.\n"
    "3. 새 표·문단을 생성(초안)할 때: ① 표는 add_table로 만든 뒤 반환된 "
    "new_table 번호로 set_cell로 셀을 채우고 autofit으로 정리하세요(치수는 "
    "직접 지정하지 말고 엔진이 계산). 헤더가 있는 양식형 데이터는 add_table의 "
    "data로 한 번에 넣어도 됩니다. ② 이미 표준 양식 표가 있으면 apply_template로 "
    "채움 칸만 채우세요. ③ 본문 문장·제목은 add_paragraph로 추가하세요. "
    "④ 내용은 공문서 규정(항목기호 순서·날짜 표기·'끝'/'이하 빈칸')을 지켜 구성하세요.\n"
    "4. 편집을 마치면 결과를 한국어로 간결히 요약해 보고하세요. 무엇을 바꿨는지 "
    "표 번호·위치와 함께 알려주세요.\n"
    "5. 지시가 모호하거나 위험한 삭제(del_table 등)면 실행 전에 사용자에게 "
    "무엇을 할지 설명하고 확인을 구하세요.\n\n"
    + GOV_DOC_RULES
)

# 편집 도구를 ops.do_op의 args 형태로 변환하는 매핑.
# 대부분 tool input이 그대로 args지만, do_op는 문자열 키를 기대하므로 그대로 넘긴다.


def _run_tool(doc, name, tool_input):
    """도구 호출 하나를 실행하고 (결과 dict, 실행된 액션 dict|None) 반환."""
    if name == "list_tables":
        return {"tables": ops.tables_summary(doc)}, None
    if name == "get_table":
        d = ops.table_detail(doc, int(tool_input["ti"]))
        return (d or {"error": "표 없음"}), None
    if name == "list_paragraphs":
        return {"paragraphs": [{"i": i, "text": t}
                               for _, _, i, t in doc.paragraphs()]}, None
    if name in EDIT_TOOL_NAMES:
        extra = ops.do_op(doc, name, tool_input)
        issues = ops.verify_issues(doc)
        result = {"ok": True, "verify": issues}
        result.update(extra)
        action = {"tool": name, "input": tool_input}
        return result, action
    return {"error": "알 수 없는 도구: %s" % name}, None


def _call_messages(api_key, model, payload, base_url="https://api.anthropic.com"):
    """Claude Messages API를 urllib로 직접 호출한다(테스트에서 목으로 교체).

    반환: 파싱된 응답 JSON(dict). 오류 시 예외를 올린다(호출부가 사용자에게 전달).
    """
    url = base_url.rstrip("/") + "/v1/messages"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise RuntimeError("Claude API 오류 %d: %s" % (e.code, detail))
    except urllib.error.URLError as e:
        raise RuntimeError("Claude API 연결 실패: %s" % e.reason)


def run_agent(doc, user_message, api_key, model="claude-opus-4-8",
              call=_call_messages):
    """자연어 지시를 받아 문서를 편집한다.

    doc          : HwpxDoc (제자리 편집됨)
    user_message : 사용자 자연어 지시
    api_key      : 사용자 Claude API 키(저장 안 함)
    model        : 기본 claude-opus-4-8
    call         : Messages API 호출 함수(테스트 주입용). 기본은 실제 urllib 호출.

    반환: {"reply": 최종 텍스트, "actions": [실행 편집], "verify": 이슈 목록}
    """
    messages = [{"role": "user", "content": user_message}]
    actions = []

    for _ in range(_MAX_TURNS):
        payload = {
            "model": model,
            "max_tokens": 8192,
            "system": _SYSTEM,
            "tools": TOOLS,
            "thinking": {"type": "adaptive"},
            "messages": messages,
        }
        resp = call(api_key, model, payload)
        content = resp.get("content", [])
        # 같은 모델 재전송 규칙: thinking 포함 content 블록 전체를 히스토리에 보존
        messages.append({"role": "assistant", "content": content})

        stop = resp.get("stop_reason")
        if stop != "tool_use":
            reply = "".join(b.get("text", "") for b in content
                            if b.get("type") == "text").strip()
            return {"reply": reply, "actions": actions,
                    "verify": ops.verify_issues(doc)}

        # tool_use 블록들을 실행하고 tool_result로 되돌린다
        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            try:
                result, action = _run_tool(doc, block["name"],
                                           block.get("input", {}))
                is_error = False
            except Exception as e:  # 편집 실패는 모델에게 알려 재시도 유도
                result = {"error": "%s: %s" % (type(e).__name__, e)}
                action = None
                is_error = True
            if action:
                actions.append(action)
            tr = {"type": "tool_result", "tool_use_id": block["id"],
                  "content": json.dumps(result, ensure_ascii=False)}
            if is_error:
                tr["is_error"] = True
            tool_results.append(tr)
        messages.append({"role": "user", "content": tool_results})

    # 상한 초과: 여기까지의 편집은 유효, 마지막 상태를 보고
    return {"reply": "편집 단계 상한(%d)에 도달해 중단했습니다. 지금까지의 "
                     "편집은 적용되었습니다." % _MAX_TURNS,
            "actions": actions, "verify": ops.verify_issues(doc)}

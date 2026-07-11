"""tools — Claude tool-use 도구 스키마(JSON Schema).

엔진 op을 Claude가 호출할 수 있는 "도구"로 노출한다. 조회 도구(list_tables/
get_table/list_paragraphs)와 편집 도구(server/ops.py::do_op의 op과 1:1)로 나뉜다.
각 도구의 description에 "언제 쓰는지"를 명확히 적어 모델이 정확히 고르게 한다.
"""

# 조회 도구 -----------------------------------------------------------------
_READ_TOOLS = [
    {
        "name": "list_tables",
        "description": "문서의 모든 표 목록(표 번호·행 수·열 수·중첩 여부)을 "
                       "돌려준다. 어떤 표를 편집할지 정하기 전에 먼저 호출해 "
                       "표 번호(ti)를 확인한다.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_table",
        "description": "특정 표의 모든 셀 내용(행·열·텍스트)을 돌려준다. 셀을 "
                       "수정하기 전에 현재 값·구조를 확인하는 데 쓴다.",
        "input_schema": {
            "type": "object",
            "properties": {"ti": {"type": "integer",
                                  "description": "표 번호(list_tables의 index)"}},
            "required": ["ti"],
        },
    },
    {
        "name": "list_paragraphs",
        "description": "표 밖 본문 문단 목록(번호·텍스트)을 돌려준다. 제목·본문 "
                       "텍스트를 확인하거나 어디를 고칠지 찾을 때 쓴다.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

# 편집 도구 (server/ops.py::do_op의 op과 동일) ------------------------------
_EDIT_TOOLS = [
    {
        "name": "set_cell",
        "description": "표의 한 셀 텍스트를 교체한다. 값 하나를 바꾸거나 채울 때 "
                       "쓴다. 예: '3번 표 2행 1열을 20으로'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ti": {"type": "integer", "description": "표 번호"},
                "row": {"type": "integer", "description": "행(0부터)"},
                "col": {"type": "integer", "description": "열(0부터)"},
                "text": {"type": "string", "description": "넣을 텍스트"},
            },
            "required": ["ti", "row", "col", "text"],
        },
    },
    {
        "name": "autofit",
        "description": "표의 열 폭·행 높이·글자 크기를 내용에 맞춰 자동 조정한다. "
                       "표 전체 폭은 유지하고, 긴 내용이 든 열만 넓힌다. 셀을 "
                       "채우거나 편집한 뒤 레이아웃을 정리할 때 호출한다.",
        "input_schema": {
            "type": "object",
            "properties": {"ti": {"type": "integer", "description": "표 번호"}},
            "required": ["ti"],
        },
    },
    {
        "name": "del_col",
        "description": "표에서 열 하나를 통째로 삭제한다(병합 인식). 예: "
                       "'현황표 담임 열 삭제'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ti": {"type": "integer", "description": "표 번호"},
                "col": {"type": "integer", "description": "삭제할 열(0부터)"},
            },
            "required": ["ti", "col"],
        },
    },
    {
        "name": "del_row",
        "description": "표에서 행 하나를 통째로 삭제한다(병합 인식).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ti": {"type": "integer", "description": "표 번호"},
                "row": {"type": "integer", "description": "삭제할 행(0부터)"},
            },
            "required": ["ti", "row"],
        },
    },
    {
        "name": "del_table",
        "description": "표 하나를 문서에서 통째로 삭제한다. 되돌리기 어려우니 "
                       "사용자가 명확히 삭제를 요청했을 때만 쓴다.",
        "input_schema": {
            "type": "object",
            "properties": {"ti": {"type": "integer", "description": "표 번호"}},
            "required": ["ti"],
        },
    },
    {
        "name": "copy_row",
        "description": "표의 한 행을 복제해 그 아래에 추가한다(스타일 상속). "
                       "명단 등 데이터가 많아 행이 더 필요할 때 쓴다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ti": {"type": "integer", "description": "표 번호"},
                "row": {"type": "integer", "description": "복제할 기준 행(0부터)"},
                "count": {"type": "integer", "description": "추가할 행 수(기본 1)"},
            },
            "required": ["ti", "row"],
        },
    },
    {
        "name": "replace_regex",
        "description": "문서 전체(표 포함)에서 정규식으로 텍스트를 치환한다. "
                       "서식은 보존한다. 예: '6학년을 5학년으로'는 "
                       r"pattern='(?<![0-9~∼·\\-])6\\s*학년', repl='5학년' 처럼 "
                       "'2026학년도' 같은 오탐을 피하도록 신중히 패턴을 짠다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "파이썬 정규식"},
                "repl": {"type": "string", "description": "치환 문자열"},
            },
            "required": ["pattern", "repl"],
        },
    },
    {
        "name": "add_table",
        "description": "새 표를 문서 끝(또는 지정 문단 뒤)에 생성한다. 초안을 만들 "
                       "때 쓴다. 생성 후 반환된 new_table 번호로 set_cell로 셀을 "
                       "채우고 autofit으로 정리한다. data로 셀을 한 번에 채울 수도 "
                       "있다. 병합 없는 균일한 표만 생성된다(생성 후 autofit이 폭·"
                       "높이를 자동 조정). 기존 표와 서식을 맞추려면 style_from에 "
                       "본뜰 표 번호를 준다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "rows": {"type": "integer", "description": "행 수"},
                "cols": {"type": "integer", "description": "열 수"},
                "data": {"type": "array",
                         "items": {"type": "array", "items": {"type": "string"}},
                         "description": "행×열 셀 텍스트(2차원 배열, 선택). "
                                        "부족한 칸은 빈 셀."},
                "after_paragraph": {"type": "integer",
                                    "description": "이 문단 번호 뒤에 삽입(생략 시 "
                                                   "문서 끝)"},
                "style_from": {"type": "integer",
                               "description": "이 표 번호의 글꼴·정렬·테두리 서식을 "
                                              "상속(선택)"},
            },
            "required": ["rows", "cols"],
        },
    },
    {
        "name": "add_paragraph",
        "description": "표 밖 본문에 새 문단을 추가한다(직전 문단의 스타일을 상속). "
                       "제목·설명 문장 등을 초안에 넣을 때 쓴다.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "문단 텍스트"}},
            "required": ["text"],
        },
    },
    {
        "name": "apply_template",
        "description": "표준 양식 표에 records를 채워 초안을 완성한다. 채움 칸만 "
                       "채우고(헤더·라벨 등 고정 칸 불변), 데이터가 많으면 행을 "
                       "자동 증설하고 autofit까지 한다. 명단 등을 양식에 넣을 때 쓴다. "
                       "records는 {라벨:값} dict 배열 또는 [값,값] 배열. 병합이 있는 "
                       "양식은 실패할 수 있다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ti": {"type": "integer", "description": "양식 표 번호"},
                "records": {"type": "array",
                            "description": "행별 데이터. 각 원소는 {헤더라벨:값} "
                                           "객체이거나 채움 열 순서의 문자열 배열."},
            },
            "required": ["ti", "records"],
        },
    },
    {
        "name": "sum_row",
        "description": "표의 한 행에서 데이터 칸 숫자를 더해 합계 칸에 넣는다. "
                       "cols 미지정 시 0열(라벨)과 합계 칸을 뺀 나머지를 더한다. "
                       "예: '시수 합계 다시 계산'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ti": {"type": "integer", "description": "표 번호"},
                "row": {"type": "integer", "description": "행(0부터)"},
                "sum_col": {"type": "integer", "description": "합계를 넣을 열"},
                "cols": {"type": "array", "items": {"type": "integer"},
                         "description": "더할 열 목록(생략 가능)"},
            },
            "required": ["ti", "row", "sum_col"],
        },
    },
]

# Claude API tools 배열
TOOLS = _READ_TOOLS + _EDIT_TOOLS

# 편집 도구 이름 집합(조회 도구와 구분해 op 실행기로 라우팅)
EDIT_TOOL_NAMES = {t["name"] for t in _EDIT_TOOLS}
READ_TOOL_NAMES = {t["name"] for t in _READ_TOOLS}

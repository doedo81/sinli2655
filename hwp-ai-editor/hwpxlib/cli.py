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

  python3 hwpx_edit.py 파일.hwpx autofit 표번호 [--min-pt 6] [--no-shrink] -o 결과.hwpx
      → 표 자동 레이아웃: 표 전체 폭은 유지한 채 내용이 긴 열만 넓히고,
        넘치면 행 높이 상향(줄바꿈) → 마지막 수단으로 그 셀 글자만 축소.
        (사람이 폭·높이를 지정하지 않아도 엔진이 치수를 자동 계산)

  python3 hwpx_edit.py 양식.hwpx template-info 표번호
      → 양식 스키마 확인: 헤더행·라벨열·채움 칸·헤더 라벨→열 매핑

  python3 hwpx_edit.py 양식.hwpx apply-template 표번호 --records "값1|값2;값1|값2" [--no-autofit] -o 결과.hwpx
      → 표준 양식 준수 편집: 데이터를 채움 칸에만 넣고(고정 칸·서식 불변),
        데이터가 많으면 행 자동 증설 → autofit 자동 맞춤 → 양식·구조 검증.
        (세미콜론=행, 파이프=채움 열 순서)

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
import sys

from .core import HwpxDoc
from .autotable import autofit_table
from .template import apply_template, extract_schema


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    path, cmd = argv[1], argv[2]
    args = argv[3:]
    out_path = path
    if "-o" in args:
        i = args.index("-o")
        out_path = args[i + 1]
        args = args[:i] + args[i + 2:]

    doc = HwpxDoc(path)

    if cmd == "list":
        for _, _, i, text in doc.paragraphs():
            print("[%d] %s" % (i, text if text.strip() else "(빈 문단)"))
    elif cmd == "tables":
        tbs = doc.tables()
        if not tbs:
            print("표가 없습니다.")
        for tb in tbs:
            print("표 %d (%d행 x %d열%s)" % (
                tb["index"], tb["rows"], tb["cols"],
                ", 중첩 표 %d개 포함" % tb["nested"] if tb["nested"] else ""))
            for c in sorted(tb["cells"], key=lambda c: (c["row"], c["col"])):
                print("  (%d,%d) %s" % (c["row"], c["col"],
                                        c["text"] if c["text"].strip() else "(빈 셀)"))
    elif cmd == "replace":
        n = doc.replace_text(args[0], args[1])
        doc.save(out_path)
        print("%d곳 바꿈 → %s" % (n, out_path))
    elif cmd == "add-table":
        # 사용법: add-table 행 열 [--data "a|b;c|d"] [--after 문단번호]
        rows, cols = int(args[0]), int(args[1])
        data = None
        after = None
        if "--data" in args:
            raw = args[args.index("--data") + 1]
            data = [row.split("|") for row in raw.split(";")]
        if "--after" in args:
            after = int(args[args.index("--after") + 1])
        kw = {}
        if "--style-from" in args:
            st = doc.table_style(int(args[args.index("--style-from") + 1]))
            kw = {"char_pr": st["charPr"], "para_pr": st["paraPr"],
                  "border_fill": st["borderFill"]}
        info = doc.add_table(rows, cols, data=data, after_paragraph=after, **kw)
        doc.save(out_path)
        print("표 생성 완료 (%d행x%d열, 테두리 서식 #%s) → %s"
              % (info["rows"], info["cols"], info["border_fill"], out_path))
    elif cmd == "set-cell":
        fit = "--fit" in args
        if fit:
            args = [a for a in args if a != "--fit"]
        text = args[3].replace("\\n", "\n").replace("\\t", "\t")
        doc.set_cell(int(args[0]), int(args[1]), int(args[2]), text)
        if fit:
            pt = doc.fit_cell(int(args[0]), int(args[1]), int(args[2]))
            doc.save(out_path)
            print("표 %s 셀(%s,%s) 교체 + 크기 자동조정(%.1fpt) → %s"
                  % (args[0], args[1], args[2], pt, out_path))
        else:
            doc.save(out_path)
            print("표 %s 셀(%s,%s) 교체 완료 → %s"
                  % (args[0], args[1], args[2], out_path))
    elif cmd == "set-cell-lines":
        lines = [l.replace("\\t", "\t")
                 for l in args[3].split("|")]
        n = doc.set_cell_paras(int(args[0]), int(args[1]), int(args[2]), lines)
        doc.save(out_path)
        print("표 %s 셀(%s,%s)에 문단 %d개 생성 → %s"
              % (args[0], args[1], args[2], n, out_path))
    elif cmd == "fit-cell":
        pt = doc.fit_cell(int(args[0]), int(args[1]), int(args[2]))
        doc.save(out_path)
        print("표 %s 셀(%s,%s) 글자 크기 %.1fpt로 맞춤 → %s"
              % (args[0], args[1], args[2], pt, out_path))
    elif cmd == "cell-font":
        doc.cell_font(int(args[0]), int(args[1]), int(args[2]), float(args[3]))
        doc.save(out_path)
        print("표 %s 셀(%s,%s) 글자 크기 %spt 적용 → %s"
              % (args[0], args[1], args[2], args[3], out_path))
    elif cmd == "verify":
        issues, fixed = doc.verify(fix="--fix" in args)
        if not issues:
            print("구조 검진: 이상 없음 (모든 표의 행·열 속성 정상)")
        else:
            for it in issues:
                print("표 %d: %s (%s)" % (it["table"], it["kind"], it["detail"]))
            if "--fix" in args:
                doc.save(out_path)
                print("→ %d개 표의 개수 속성 자동 수정 완료 → %s"
                      % (fixed, out_path))
            else:
                print("→ 자동 수정하려면: verify --fix -o 결과.hwpx")
    elif cmd == "rules":
        print(GOV_DOC_RULES)
    elif cmd == "cell-style":
        st = doc.cell_style(int(args[0]), int(args[1]), int(args[2]))
        det = doc._para_details(st["paraPr"]) if st["paraPr"] else {}
        extra = ", 줄간격 %s" % det["spacing"] if det.get("spacing") else ""
        for k in ("들여쓰기", "왼쪽여백", "문단위", "문단아래"):
            if det.get(k):
                extra += ", %s %.1fpt" % (k, det[k])
        print("표 %s 셀(%s,%s): 글꼴 %s, %.1fpt, 장평 %s%%, %s 정렬%s"
              % (args[0], args[1], args[2], st["font"], st["size"],
                 st["ratio"], st["align"], extra))
    elif cmd == "para-info":
        paras = doc.paragraphs()
        i = int(args[0])
        sec, (s, e), _, text = paras[i]
        xml = doc.files[sec].decode("utf-8")
        import re as _re
        pm = _re.match(r'<\w+:p\b[^>]*\bparaPrIDRef="(\d+)"', xml[s:e])
        det = doc._para_details(pm.group(1)) if pm else {}
        parts = ["%s: %s" % (k, v) for k, v in det.items()]
        print("문단 %d (%s...): %s" % (i, text[:15], ", ".join(parts) or "정보 없음"))
    elif cmd == "para-prop" or cmd == "cell-prop":
        def _opts(a):
            kw = {}
            m = {"--spacing": ("spacing", int), "--align": ("align", str),
                 "--indent": ("indent", float), "--left": ("left", float),
                 "--right": ("right", float), "--before": ("prev", float),
                 "--after": ("nxt", float)}
            for flag, (key, cast) in m.items():
                if flag in a:
                    kw[key] = cast(a[a.index(flag) + 1])
            return kw
        kw = _opts(args)
        if not kw:
            print("옵션 필요: --spacing 123 / --align 가운데 / --indent pt / "
                  "--left pt / --before pt / --after pt")
            return 1
        if cmd == "para-prop":
            doc.para_prop(int(args[0]), **kw)
            doc.save(out_path)
            print("문단 %s 속성 변경 %s → %s" % (args[0], kw, out_path))
        else:
            doc.cell_prop(int(args[0]), int(args[1]), int(args[2]), **kw)
            doc.save(out_path)
            print("표 %s 셀(%s,%s) 속성 변경 %s → %s"
                  % (args[0], args[1], args[2], kw, out_path))
    elif cmd == "copy-style":
        font, size, ratio = doc.copy_style(int(args[0]), int(args[1]),
                                           int(args[2]), int(args[3]),
                                           int(args[4]))
        doc.save(out_path)
        print("표 %s 셀(%s,%s)에 (%s,%s) 스타일 적용: %s %.1fpt → %s"
              % (args[0], args[1], args[2], args[3], args[4],
                 font, size, out_path))
    elif cmd == "check-table":
        if args and args[0] != "all":
            targets = [int(args[0])]
        else:
            targets = range(len(doc.tables()))
        for ti in targets:
            r = doc.check_table(ti)
            if r["dominant"] is None:
                continue
            f, s, a = r["dominant"]
            if r["deviations"]:
                print("표 %d: 대표 스타일 %s %.1fpt %s정렬 (%d셀)"
                      % (ti, f, s, a, r["count"]))
                for (df, ds, da), cells in r["deviations"]:
                    loc = ", ".join("(%d,%d)" % rc for rc in cells[:6])
                    more = " 외 %d곳" % (len(cells) - 6) if len(cells) > 6 else ""
                    print("   ⚠ 이탈: %s %.1fpt %s정렬 → %s%s"
                          % (df, ds, da, loc, more))
    elif cmd == "para-font":
        doc.para_font(int(args[0]), float(args[1]))
        doc.save(out_path)
        print("문단 %s 글자를 %spt로 통일 → %s" % (args[0], args[1], out_path))
    elif cmd == "del-table":
        doc.del_table(int(args[0]))
        doc.save(out_path)
        print("표 %s 통째 삭제 완료 → %s" % (args[0], out_path))
    elif cmd == "del-col":
        doc.del_col(int(args[0]), int(args[1]))
        doc.save(out_path)
        print("표 %s의 열 %s 삭제 완료 → %s" % (args[0], args[1], out_path))
    elif cmd == "del-para":
        removed = doc.del_para(int(args[0]))
        doc.save(out_path)
        print("문단 %s 삭제 완료 (내용: %s) → %s"
              % (args[0], (removed[:20] + "...") if len(removed) > 20
                 else removed or "(빈 문단)", out_path))
    elif cmd == "del-row":
        doc.del_row(int(args[0]), int(args[1]))
        doc.save(out_path)
        print("표 %s의 행 %s 삭제 완료 → %s" % (args[0], args[1], out_path))
    elif cmd == "clear-row":
        ti, r = int(args[0]), int(args[1])
        tb = doc.tables()[ti]
        cols = sorted({c["col"] for c in tb["cells"] if c["row"] == r})
        for c in cols:
            try:
                doc.set_cell(ti, r, c, "")
            except (ValueError, IndexError):
                pass
        doc.save(out_path)
        print("표 %s의 행 %s 내용 비움 (%d칸) → %s" % (args[0], args[1],
                                                       len(cols), out_path))
    elif cmd == "set-para":
        doc.set_paragraph(int(args[0]), args[1])
        doc.save(out_path)
        print("문단 %s 교체 완료 → %s" % (args[0], out_path))
    elif cmd == "add-para":
        doc.add_paragraph(args[0])
        doc.save(out_path)
        print("문단 추가 완료 → %s" % out_path)
    elif cmd == "autofit":
        # autofit 표번호 [--min-pt 6] [--no-shrink]
        min_pt = float(args[args.index("--min-pt") + 1]) if "--min-pt" in args else 6.0
        allow_shrink = "--no-shrink" not in args
        rep = autofit_table(doc, int(args[0]), min_pt=min_pt,
                            allow_shrink=allow_shrink)
        doc.save(out_path)
        print("표 %s 자동 맞춤: 열폭 %s, 글자축소 %d칸 → %s"
              % (args[0], rep["widths"], len(rep["shrunk"]), out_path))
    elif cmd == "apply-template":
        # apply-template 표번호 --records "김철수|총무과;이영희|기획과" [--no-autofit]
        raw = args[args.index("--records") + 1]
        records = [row.split("|") for row in raw.split(";")]
        autofit = "--no-autofit" not in args
        rep = apply_template(doc, int(args[0]), records, autofit=autofit)
        doc.save(out_path)
        print("양식 적용: 행 +%d, %d칸 채움, 문제 %d건 → %s"
              % (rep["added_rows"], rep["filled"], len(rep["issues"]), out_path))
        for it in rep["issues"]:
            print("  ⚠ %s %s" % (it["kind"], it.get("detail", "")))
    elif cmd == "template-info":
        sch = extract_schema(doc, int(args[0]))
        print("열 %d · 헤더행 %s · 라벨열 %s"
              % (sch["cols"], sch["header_rows"], sch["label_cols"]))
        print("채움열 %s · 데이터행 %s · 반복행 %s"
              % (sch["fill_cols"], sch["data_rows"], sch["repeat_row"]))
        print("헤더 라벨→열: %s" % sch["label_to_col"])
        print("채움 칸: %s" % sorted(sch["fillable"]))
    else:
        print("알 수 없는 명령: %s" % cmd)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

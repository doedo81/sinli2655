"""테스트용 최소 HWPX 픽스처 생성기.

엔진(HwpxDoc)이 요구하는 최소 구성만 담는다:
  - mimetype
  - Contents/header.xml  (charPr/paraPr/borderFill 정의)
  - Contents/section0.xml (문단 + 표)
한/글로 실제로 열려면 더 많은 파일이 필요하지만, 엔진 로직 검증에는 충분하다.
"""
import io
import zipfile

_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">
 <hh:refList>
  <hh:fontfaces itemCnt="1">
   <hh:fontface lang="HANGUL" fontCnt="1">
    <hh:font id="0" face="함초롬바탕" type="TTF"/>
   </hh:fontface>
  </hh:fontfaces>
  <hh:charProperties itemCnt="1">
   <hh:charPr id="0" height="1000" textColor="#000000" useFontSpace="0">
    <hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>
    <hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>
   </hh:charPr>
  </hh:charProperties>
  <hh:paraProperties itemCnt="1">
   <hh:paraPr id="0" tabPrIDRef="0" condense="0">
    <hh:align horizontal="LEFT" vertical="BASELINE"/>
    <hh:margin><hh:intent value="0" unit="HWPUNIT"/><hh:left value="0" unit="HWPUNIT"/><hh:right value="0" unit="HWPUNIT"/><hh:prev value="0" unit="HWPUNIT"/><hh:next value="0" unit="HWPUNIT"/></hh:margin>
    <hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>
   </hh:paraPr>
  </hh:paraProperties>
  <hh:borderFills itemCnt="1">
   <hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
    <hh:slash type="NONE" Crooked="0" isCounter="0"/>
    <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
   </hh:borderFill>
  </hh:borderFills>
 </hh:refList>
</hh:head>"""


def _tc(col, row, width, height, text):
    return (
        '<hp:tc borderFillIDRef="1">'
        '<hp:cellAddr colAddr="%d" rowAddr="%d"/>'
        '<hp:cellSpan colSpan="1" rowSpan="1"/>'
        '<hp:cellSz width="%d" height="%d"/>'
        '<hp:subList>'
        '<hp:p paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">'
        '<hp:t>%s</hp:t></hp:run></hp:p>'
        '</hp:subList></hp:tc>' % (col, row, width, height, text))


def make_sample_hwpx(rows_data=None, col_width=8000, row_height=2000):
    """rows_data: 2차원 리스트(행×열)의 셀 텍스트. 기본은 3열 2행 표."""
    if rows_data is None:
        rows_data = [
            ["성명", "부서", "비고"],
            ["홍길동",
             "행정지원과 문서관리팀 주무관",
             "아주 길고 긴 특이사항 내용이 이 칸에 들어갑니다 확인용"],
        ]
    nrows = len(rows_data)
    ncols = max(len(r) for r in rows_data)
    total_w = col_width * ncols
    total_h = row_height * nrows
    trs = []
    for r, row in enumerate(rows_data):
        tcs = "".join(_tc(c, r, col_width, row_height,
                          row[c] if c < len(row) else "")
                      for c in range(ncols))
        trs.append("<hp:tr>%s</hp:tr>" % tcs)
    tbl = (
        '<hp:tbl id="100" rowCnt="%d" colCnt="%d" borderFillIDRef="1" '
        'pageBreak="CELL" repeatHeader="0">'
        '<hp:sz width="%d" height="%d"/>%s</hp:tbl>'
        % (nrows, ncols, total_w, total_h, "".join(trs)))
    section = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
        '<hp:p paraPrIDRef="0" styleIDRef="0" id="1"><hp:run charPrIDRef="0">'
        '<hp:t>표 자동맞춤 테스트 문서</hp:t></hp:run></hp:p>'
        '<hp:p paraPrIDRef="0" styleIDRef="0" id="2"><hp:run charPrIDRef="0">'
        + tbl +
        '</hp:run></hp:p>'
        '</hs:sec>')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), b"application/hwp+zip",
                    compress_type=zipfile.ZIP_STORED)
        zf.writestr("Contents/header.xml", _HEADER)
        zf.writestr("Contents/section0.xml", section)
    return buf.getvalue()

"""blank — 빈 HWPX 문서를 무(無)에서 생성.

한/글이 여는 유효한 HWPX(OPC/OWPML 패키지)의 **필수 뼈대 8종**을 개인정보 없이
합성한다. 실파일에서 파악한 포맷만 재현하며, 본문·이미지·미리보기·제목 등 실제
내용은 담지 않는다. 생성 후 HwpxDoc으로 로드해 add_table/add_paragraph로 채운다.

포함 파일:
  mimetype                (STORED, application/hwp+zip)
  version.xml             HCFVersion (표준)
  settings.xml            앱 설정 (표준, 개인정보 없음)
  META-INF/container.xml  rootfile = content.hpf
  META-INF/manifest.xml   빈 odf:manifest
  Contents/content.hpf    OPF 패키지 (metadata 공란 + manifest + spine)
  Contents/header.xml     스타일 refList (완전 최소: 각 종류 1개 이상)
  Contents/section0.xml   secPr(쪽 설정) + 빈 문단 1개

한/글 호환의 최종 확인은 생성 파일을 한/글에서 1회 열어보는 것으로 한다.
문제가 있으면 header refList나 secPr 요소를 보강하거나, hwpxlib/assets/blank.hwpx에
한/글이 저장한 빈 문서를 넣으면 그 파일이 우선 사용된다(HwpxDoc.new 참고).
"""
import io
import os
import zipfile

_XMLDECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'

# HWPX 루트 요소에 쓰이는 공통 네임스페이스(실파일 기준)
_NS = (
    ' xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app"'
    ' xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
    ' xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph"'
    ' xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
    ' xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"'
    ' xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"'
    ' xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history"'
    ' xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page"'
    ' xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
    ' xmlns:hc10="http://www.hancom.co.kr/hwpml/2016/core"'
)

_VERSION = (_XMLDECL +
    '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
    'tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="1" '
    'buildNumber="0" os="1" xmlVersion="1.5" application="hwp-ai-editor" '
    'appVersion="1.0"/>')

_SETTINGS = (_XMLDECL +
    '<ha:HWPApplicationSetting '
    'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">'
    '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/>'
    '</ha:HWPApplicationSetting>')

_CONTAINER = (_XMLDECL +
    '<ocf:container '
    'xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" '
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf">'
    '<ocf:rootfiles>'
    '<ocf:rootfile full-path="Contents/content.hpf" '
    'media-type="application/hwpml-package+xml"/>'
    '</ocf:rootfiles></ocf:container>')

_MANIFEST = (_XMLDECL +
    '<odf:manifest '
    'xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>')

# content.hpf — 파일 집합을 우리가 통제하므로 뼈대 3종만 참조. metadata 공란.
_CONTENT_HPF = (_XMLDECL +
    '<opf:package'
    ' xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app"'
    ' xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
    ' xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"'
    ' xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head"'
    ' xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
    ' xmlns:opf="http://www.idpf.org/2007/opf/"'
    ' version="" unique-identifier="" id="">'
    '<opf:metadata>'
    '<opf:title xml:space="preserve"></opf:title>'
    '<opf:language>ko</opf:language>'
    '</opf:metadata>'
    '<opf:manifest>'
    '<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
    '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>'
    '<opf:item id="settings" href="settings.xml" media-type="application/xml"/>'
    '</opf:manifest>'
    '<opf:spine>'
    '<opf:itemref idref="header" linear="yes"/>'
    '<opf:itemref idref="section0" linear="yes"/>'
    '</opf:spine></opf:package>')


def _fontfaces():
    """7개 언어별 폰트면(각 1개, 함초롬바탕). id는 모두 0으로 통일."""
    langs = ["HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER"]
    faces = "".join(
        '<hh:fontface lang="%s" fontCnt="1">'
        '<hh:font id="0" face="함초롬바탕" type="TTF" isEmbedded="0">'
        '<hh:typeInfo familyType="FCAP_UNKNOWN" weight="0" proportion="0" '
        'contrast="0" strokeVariation="0" armStyle="0" letterform="0" '
        'midline="0" xHeight="0"/></hh:font></hh:fontface>' % lang
        for lang in langs)
    return '<hh:fontfaces itemCnt="7">%s</hh:fontfaces>' % faces


def _border_fills():
    """borderFill 2종. id=1은 secPr pageBorderFill·표 셀이 참조."""
    def bf(i):
        sides = "".join(
            '<hh:%s type="NONE" width="0.1 mm" color="#000000"/>' % s
            for s in ("leftBorder", "rightBorder", "topBorder", "bottomBorder"))
        return ('<hh:borderFill id="%d" threeD="0" shadow="0" centerLine="NONE" '
                'breakCellSeparateLine="0">'
                '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
                '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
                '%s'
                '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>'
                '</hh:borderFill>' % (i, sides))
    return '<hh:borderFills itemCnt="2">%s%s</hh:borderFills>' % (bf(1), bf(2))


def _char_props():
    """charPr id=0 — 함초롬바탕 10pt(height 1000)."""
    ref = ('<hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" '
           'other="0" symbol="0" user="0"/>')
    ratio = ('<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" '
             'other="100" symbol="100" user="100"/>')
    spc = ('<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" '
           'other="0" symbol="0" user="0"/>')
    rel = ('<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" '
           'other="100" symbol="100" user="100"/>')
    off = ('<hh:offset hangul="0" latin="0" hanja="0" japanese="0" '
           'other="0" symbol="0" user="0"/>')
    return ('<hh:charProperties itemCnt="1">'
            '<hh:charPr id="0" height="1000" textColor="#000000" '
            'shadeColor="none" useFontSpace="0" useKerning="0" '
            'symMark="NONE" borderFillIDRef="2">'
            '%s%s%s%s%s</hh:charPr></hh:charProperties>'
            % (ref, ratio, spc, rel, off))


def _tab_props():
    """tabPr id=0 — 자동 탭."""
    return ('<hh:tabProperties itemCnt="1">'
            '<hh:tabPr id="0" autoTabStop="1" leftTabStop="0" '
            'rightTabStop="0"/></hh:tabProperties>')


def _numberings():
    """numbering id=1 — 개요(outline). secPr outlineShapeIDRef=1이 참조."""
    paras = "".join(
        '<hh:paraHead start="1" level="%d" align="LEFT" useInstWidth="1" '
        'autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" '
        'textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" '
        'checkable="0">^%d.</hh:paraHead>' % (lv, lv)
        for lv in range(1, 8))
    return ('<hh:numberings itemCnt="1">'
            '<hh:numbering id="1" start="0">%s</hh:numbering>'
            '</hh:numberings>' % paras)


def _bullets():
    """bullet id=1."""
    return ('<hh:bullets itemCnt="1">'
            '<hh:bullet id="1" char="●" useImage="0" checkedChar="0">'
            '<hh:paraHead start="0" level="0" align="LEFT" useInstWidth="1" '
            'autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" '
            'textOffset="50"/></hh:bullet></hh:bullets>')


def _para_props():
    """paraPr id=0 — 양쪽 정렬, 줄간격 160%."""
    return ('<hh:paraProperties itemCnt="1">'
            '<hh:paraPr id="0" tabPrIDRef="0" condense="0" '
            'fontLineHeight="0" snapToGrid="1" suppressLineNumbers="0" '
            'checked="0">'
            '<hh:align horizontal="JUSTIFY" vertical="BASELINE"/>'
            '<hh:heading type="NONE" idRef="0" level="0"/>'
            '<hh:breakSetting breakLatinWord="KEEP_WORD" '
            'breakNonLatinWord="KEEP_WORD" widowOrphan="0" '
            'keepWithNext="0" keepLines="0" pageBreakBefore="0" '
            'lineWrap="BREAK"/>'
            '<hh:margin>'
            '<hh:intent value="0" unit="HWPUNIT"/>'
            '<hh:left value="0" unit="HWPUNIT"/>'
            '<hh:right value="0" unit="HWPUNIT"/>'
            '<hh:prev value="0" unit="HWPUNIT"/>'
            '<hh:next value="0" unit="HWPUNIT"/></hh:margin>'
            '<hh:lineSpacing type="PERCENT" value="160" unit="HWPUNIT"/>'
            '<hh:border borderFillIDRef="2" offsetLeft="0" offsetRight="0" '
            'offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/>'
            '</hh:paraPr></hh:paraProperties>')


def _styles():
    """style id=0 — 바탕글."""
    return ('<hh:styles itemCnt="1">'
            '<hh:style id="0" type="PARA" name="바탕글" engName="Normal" '
            'paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" '
            'langID="1042" lockForm="0"/></hh:styles>')


def _header():
    ref_list = (_fontfaces() + _border_fills() + _char_props() + _tab_props()
                + _numberings() + _bullets() + _para_props() + _styles())
    return (_XMLDECL +
            '<hh:head' + _NS + ' version="1.31" secCnt="1">'
            '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" '
            'equation="1"/>'
            '<hh:refList>' + ref_list + '</hh:refList>'
            '<hh:compatibleDocument targetProgram="HWP201X">'
            '<hh:layoutCompatibility/></hh:compatibleDocument>'
            '</hh:head>')


# secPr — 실파일에서 파악한 표준 쪽 설정(개인정보 없음). IDRef는 최소 헤더에 맞춰
# 조정: outlineShapeIDRef=1(numbering), pageBorderFill borderFillIDRef=1.
_SECPR = (
    '<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" '
    'tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" '
    'outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" '
    'masterPageCnt="0">'
    '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0" strtnum="0"/>'
    '<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
    '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" '
    'hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" '
    'hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>'
    '<hp:lineNumberShape restartType="0" countBy="0" distance="0" '
    'startNumber="0"/>'
    '<hp:pagePr landscape="WIDELY" width="59528" height="84188" '
    'gutterType="LEFT_ONLY">'
    '<hp:margin header="4252" footer="4252" gutter="0" left="8504" '
    'right="8504" top="5668" bottom="4252"/></hp:pagePr>'
    '<hp:footNotePr>'
    '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" '
    'supscript="0"/>'
    '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="850" belowLine="567" aboveLine="567"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr>'
    '<hp:endNotePr>'
    '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" '
    'supscript="0"/>'
    '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="850" belowLine="567" aboveLine="567"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr>'
    '<hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '<hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '<hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill></hp:secPr>')

# 섹션: 첫 문단의 run 안에 secPr + colPr, 이어서 빈 텍스트.
_SECTION0 = (_XMLDECL +
    '<hs:sec' + _NS + '>'
    '<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" '
    'columnBreak="0" merged="0">'
    '<hp:run charPrIDRef="0">'
    + _SECPR +
    '<hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" '
    'sameSz="1" sameGap="0"/></hp:ctrl>'
    '<hp:t></hp:t>'
    '</hp:run>'
    '<hp:linesegarray>'
    '<hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" '
    'baseline="850" spacing="600" horzpos="0" horzsize="42520" flags="393216"/>'
    '</hp:linesegarray>'
    '</hp:p>'
    '</hs:sec>')


def blank_hwpx_bytes():
    """한/글이 여는 유효한 빈 HWPX(패키지) 바이트를 생성한다(개인정보 없음)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype은 반드시 첫 항목·무압축(STORED)
        zf.writestr(zipfile.ZipInfo("mimetype"), b"application/hwp+zip",
                    compress_type=zipfile.ZIP_STORED)
        zf.writestr("version.xml", _VERSION)
        zf.writestr("settings.xml", _SETTINGS)
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr("META-INF/manifest.xml", _MANIFEST)
        zf.writestr("Contents/content.hpf", _CONTENT_HPF)
        zf.writestr("Contents/header.xml", _header())
        zf.writestr("Contents/section0.xml", _SECTION0)
    return buf.getvalue()


def seed_path():
    """사용자 제공 씨앗 양식 경로(있으면 우선 사용). hwpxlib/assets/blank.hwpx."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "blank.hwpx")

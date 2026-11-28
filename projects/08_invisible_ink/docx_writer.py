"""Write a real Word (.docx) file with the standard library alone.

The book uses the python-docx package, which isn't one the browser's
Python ships with. Luckily a .docx file is only a zip of a few small XML
files, so ``zipfile`` and some careful strings do the job:

* ``[Content_Types].xml`` says what each part is;
* ``_rels/.rels`` points at the document;
* ``word/document.xml`` holds the paragraphs;
* ``word/styles.xml`` sets one font and size for everything, so the
  hidden lines are exactly as wide as the visible ones would be.

Each line becomes its own paragraph with no space before or after it
(the book's ``set_spacing``), and a hidden line's text is white.
"""

import io
import zipfile
from xml.sax.saxutils import escape

WHITE = "FFFFFF"
FONT = "Georgia"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" \
ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" \
ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" \
Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" \
Target="word/document.xml"/>
</Relationships>"""

DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" \
Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" \
Target="styles.xml"/>
</Relationships>"""

STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
<w:docDefaults>
<w:rPrDefault><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/>\
<w:sz w:val="22"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr>\
<w:spacing w:before="0" w:after="0" w:line="300" w:lineRule="auto"/>\
</w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
</w:styles>"""


def run(
    text: str, *, colour: str | None = None, bold: bool = False, size: int | None = None
) -> str:
    """One run of text in one style (a "run" in Word's own words)."""
    props = ""
    if bold:
        props += "<w:b/>"
    if colour:
        props += f'<w:color w:val="{colour}"/>'
    if size:
        props += f'<w:sz w:val="{size}"/>'
    rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def paragraph(runs: str = "", *, centred: bool = False) -> str:
    """One paragraph (one press of Enter), with no extra space above or below it."""
    align = '<w:jc w:val="center"/>' if centred else ""
    return f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/>{align}</w:pPr>{runs}</w:p>'


def letter_xml(letter: list[dict], title: str, subtitle: str = "", date: str = "") -> str:
    """The document's body: a letterhead, then one paragraph per line of the letter."""
    parts = [paragraph(run(title, bold=True, size=40), centred=True)]
    if subtitle:
        parts.append(paragraph(run(subtitle, size=18), centred=True))
    parts.append(paragraph())
    if date:
        parts += [paragraph(run(date)), paragraph()]
    for line in letter:
        text = line["text"]
        parts.append(paragraph(run(text, colour=WHITE if line["hidden"] else None) if text else ""))
    body = "".join(parts)
    page = '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" \
w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<w:document xmlns:w="{W}"><w:body>{body}{page}</w:body></w:document>'
    )


def make_docx(letter: list[dict], title: str, subtitle: str = "", date: str = "") -> bytes:
    """Zip the parts into a .docx file and return its bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", CONTENT_TYPES)
        docx.writestr("_rels/.rels", RELS)
        docx.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS)
        docx.writestr("word/document.xml", letter_xml(letter, title, subtitle, date))
        docx.writestr("word/styles.xml", STYLES)
    return buffer.getvalue()

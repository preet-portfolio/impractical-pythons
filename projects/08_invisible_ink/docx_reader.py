"""Look inside any Word (.docx) file for white ink.

The detective's side of the trick. A .docx is a zip; its words live in
``word/document.xml``, one ``<w:p>`` per paragraph and one ``<w:r>``
("run") per stretch of text in one style. A run whose colour is white
(or one marked "hidden", Word's own vanishing ink) is reported as ink.
"""

import io
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
INVISIBLE = {"FFFFFF", "FEFEFE", "FDFDFD"}  # white, and white that hopes you won't check
BIGGEST = 5_000_000  # bytes: a letter is tiny; anything bigger is not for this counter


class NotALetter(ValueError):
    """The file can't be read as a Word document."""


def run_is_ink(run: ET.Element) -> bool:
    """Whether a run is written in white (or Word's "hidden" text)."""
    props = run.find(f"{W}rPr")
    if props is None:
        return False
    colour = props.find(f"{W}color")
    if colour is not None and colour.get(f"{W}val", "").upper() in INVISIBLE:
        return True
    return props.find(f"{W}vanish") is not None


def read_paragraphs(data: bytes) -> list[dict]:
    """Every paragraph as ``{"text", "ink"}``: all its words, and just its white ones."""
    if len(data) > BIGGEST:
        raise NotALetter("That file is far too big to be a letter.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as docx:
            if docx.getinfo("word/document.xml").file_size > BIGGEST:
                raise NotALetter("That file is far too big to be a letter.")
            xml = docx.read("word/document.xml")
        # Word never writes a DOCTYPE. Refusing one shuts out entity tricks
        # ("billion laughs", outside files) before the parser sees them.
        if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
            raise NotALetter("That file has something odd inside it, so the shop won't open it.")
        root = ET.fromstring(xml)
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as error:
        raise NotALetter("That doesn't look like a Word letter (a .docx file).") from error
    paragraphs = []
    for para in root.iter(f"{W}p"):
        text, ink = [], []
        for run in para.iter(f"{W}r"):
            words = "".join(t.text or "" for t in run.iter(f"{W}t"))
            text.append(words)
            if run_is_ink(run):
                ink.append(words)
        paragraphs.append({"text": "".join(text), "ink": "".join(ink)})
    return paragraphs


def find_white_ink(data: bytes) -> list[str]:
    """The white ink in a .docx file, one entry per paragraph that has any."""
    return [p["ink"] for p in read_paragraphs(data) if p["ink"].strip()]

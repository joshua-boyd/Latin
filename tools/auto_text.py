#!/usr/bin/env python3
"""Pull De Re Publica and De Legibus out of their sources as (book, section, text).

Neither work is in any annotated corpus, so the raw text has to come from
elsewhere and be parsed by machine afterwards:

*De Re Publica*  Perseus TEI, which nests <div subtype="section"> inside
                 <div subtype="book"> and marks the lost stretches with
                 <gap/>. That is exactly the book-and-section citation the
                 work is referred to by.

*De Legibus*     Perseus has only a stub directory for this one, so the text
                 comes from The Latin Library, where sections are marked in
                 the running HTML as <a name="N"></a>[N].
"""

import html
import re
import xml.etree.ElementTree as ET

TEI = "{http://www.tei-c.org/ns/1.0}"
DROP = {TEI + "note", TEI + "head", TEI + "bibl", TEI + "ref", TEI + "pb",
        TEI + "cb", TEI + "gap", TEI + "figure", TEI + "label"}


def _text(el):
    """Concatenate an element's text, skipping apparatus.

    <emph> can split a word ("<emph>im</emph>petu"), so the pieces are joined
    without inserting anything between them.
    """
    out = [el.text or ""]
    for child in el:
        if child.tag not in DROP:
            out.append(_text(child))
        out.append(child.tail or "")
    return "".join(out)


def clean(s):
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\[[^\]]*\]", " ", s)         # section numbers, supplements
    s = re.sub(r"[.]\s*[.]\s*[.]", " … ", s)  # lacuna dots
    # Conjectural readings are printed in angle brackets ("<nimia>"). Keep the
    # word, drop the brackets: they only confuse the tokeniser.
    s = s.replace("<", " ").replace(">", " ").replace("*", " ")
    s = re.sub(r"\s+([,;:.!?])", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def de_re_publica(path):
    """Perseus TEI -> [(book, section, text)]."""
    root = ET.parse(path).getroot()
    out = []
    for book in root.iter(TEI + "div"):
        if book.get("subtype") != "book":
            continue
        bn = book.get("n")
        if not bn or not bn.isdigit():
            continue
        for sec in book.iter(TEI + "div"):
            if sec.get("subtype") != "section":
                continue
            sn = sec.get("n")
            body = clean(_text(sec))
            if sn and body:
                out.append((int(bn), sn, body))
    return out


SEC_RE = re.compile(r'<a\s+name="(\d+)"\s*>\s*</a>', re.I)
NAV_RE = re.compile(r"(?is)<p\s+class=(?:margin|smallborder)[^>]*>.*?(?:</p>|(?=<p))")
FOOTER_RE = re.compile(r"(?is)<div\s[^>]*class=[\"']?footer|The Classics Page")
TAG_RE = re.compile(r"<[^>]+>")

LEADING_NUMERAL = re.compile(r"^[IVXLC]+\.?\s+(?=[A-Z])")


def de_legibus(paths):
    """The Latin Library HTML -> [(book, section, text)]."""
    out = []
    for bn, path in enumerate(paths, start=1):
        raw = open(path, encoding="latin-1").read()
        cut = FOOTER_RE.search(raw)
        if cut:
            raw = raw[:cut.start()]
        # Drop the tables of section links that top and tail the text; the
        # opening speaker label sits between them and the first anchor, so
        # cutting at the anchor instead would throw it away.
        body = NAV_RE.sub(" ", raw)

        pieces = SEC_RE.split(body)
        # split() gives [before, n1, chunk1, n2, chunk2, ...]
        for i in range(1, len(pieces) - 1, 2):
            sn = pieces[i]
            chunk = pieces[i + 1]
            # A speaker label printed before the anchor belongs to this
            # section, not the one before it.
            lead = re.search(r"(?is)<b>([^<]{2,30}?:)</b>\s*$", pieces[i - 1])
            txt = clean(TAG_RE.sub(" ", chunk))
            txt = LEADING_NUMERAL.sub("", txt)
            if lead:
                txt = clean(lead.group(1)) + " " + txt
            if txt:
                out.append((bn, sn, txt))
    return out

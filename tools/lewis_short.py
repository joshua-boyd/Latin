#!/usr/bin/env python3
"""Extract short English glosses from the Perseus Lewis & Short TEI file.

L&S entries are long and citation-heavy. Unlike LSJ, they carry no <tr>
elements; the editors' own translations are simply set in italics inside the
first sense:

    <entryFree key="abdo"><orth>abdo</orth>, <itype>didi, ditum</itype>,
    <pos>v. a.</pos>, <sense n="I"><hi rend="ital">to put away</hi>,
    <hi rend="ital">remove</hi>, <hi rend="ital">set aside</hi>: ...

So the job is to pick the italic runs that are English definitions and reject
the ones that are Latin — cited forms, variant spellings, cognates. Three
things do most of that work: quotations live inside <cit>/<quote> and are
dropped wholesale, Latin set in italics almost always keeps its vowel-quantity
marks, and anything reachable from <etym> is a cognate rather than a meaning.
"""

import glob
import os
import re
import unicodedata
import xml.etree.ElementTree as ET

ENTRY_RE = re.compile(r"<entryFree\b.*?</entryFree>", re.S)
KEY_RE = re.compile(r'\bkey="([^"]*)"')

# elements whose content is never part of a gloss
DROP = {"bibl", "cit", "quote", "foreign", "etym", "gramGrp", "gram", "orth",
        "gen", "date", "author", "title", "biblScope", "pb", "cb", "ref",
        "itype", "pron", "usg", "abbr", "case", "number", "mood", "tns",
        "per", "cross", "sic", "corr", "reg", "note"}

ENGLISH_OK = re.compile(r"^[A-Za-z0-9 ,;:'’&()/.\-—…!?\[\]]+$")

# The same italics carry the entry's morphological apparatus ("gen. plur.",
# "2d pers. sing.", "Part. gen. plur. sync.") and its cross-references. A run
# built entirely out of this shorthand is never a definition.
GRAM = frozenset("""
pers person sing sg plur pl dual nom gen dat acc abl voc loc case
masc fem neut act pass mid dep depon indic ind subj conj imper imperat imp
inf infin part partic ptc sup supin gerund gerundive pres praes imperf perf
perff plup pluperf fut futur tempp temp sync syncop contr irreg regul
v verb adj adv subst num numer prep interj pron pronom particle
demonstr demonstrat interrog relat indef reflex partt cum
comp compar superl posit positive neutr impers init fin medial
collat ante post class arch archaic obsol rare abbrev orig
st nd rd th obj possess poss sc absol abs dim freq intens ext
trop fig lit poet cf id ib sq etc prob q s e g i ex lat gr eng hebr
""".split())

ORDINAL = re.compile(r"^\d+(st|nd|rd|d|th)?$", re.I)
ROMAN = re.compile(r"^(I{2,3}|IV|VI{0,3}|IX|XI{0,3})$")
WORD_RE = re.compile(r"[A-Za-z0-9]+")


def apparatus(txt):
    """True if every token is grammatical shorthand rather than English."""
    toks = WORD_RE.findall(txt)
    if not toks:
        return True
    return all(t.lower() in GRAM or len(t) == 1 or ORDINAL.match(t) for t in toks)


def cross_reference(txt):
    """'v. exeo, II' and friends point at another entry instead of glossing."""
    return any(ROMAN.match(t) for t in WORD_RE.findall(txt))

# vowels the dictionary marks for quantity; their presence means the run is
# Latin being quoted, not English being offered as a translation
QUANTITY_MARKS = frozenset("̄̆")


def clean(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[\s,;:.\-—]+", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+([,;.])", r"\1", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(" ,;:.—- ")


def is_latin_form(txt):
    return any(c in QUANTITY_MARKS for c in unicodedata.normalize("NFD", txt))


def usable(txt, key):
    """Keep plain-English glosses; drop Latin forms, cognates and stubs."""
    if not txt or len(txt) < 3 or len(txt) > 120:
        return False
    if not ENGLISH_OK.match(txt):
        return False
    if is_latin_form(txt) or apparatus(txt) or cross_reference(txt):
        return False
    # A one-word italic that merely repeats the headword is a variant spelling.
    if " " not in txt and txt.lower().rstrip(".").startswith(key.lower()[:4]):
        return False
    return any(c.isalpha() for c in txt)


def italics(sense, skip):
    """Italic runs inside a sense, minus any in a quotation or etymology."""
    out = []
    for hi in sense.iter("hi"):
        if hi.get("rend") != "ital" or id(hi) in skip:
            continue
        out.append(clean("".join(hi.itertext())))
    return out


def unwanted(root):
    """Every element inside a construct that never holds a definition."""
    skip = set()
    for parent in root.iter():
        if parent.tag in DROP:
            for child in parent.iter():
                skip.add(id(child))
    return skip


def gloss_from_entry(xml, key):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None

    skip = unwanted(root)
    senses = list(root.iter("sense")) or [root]

    glosses = []
    for sense in senses[:3]:
        for txt in italics(sense, skip):
            if usable(txt, key) and txt.lower() not in (g.lower() for g in glosses):
                glosses.append(txt)
        if len(glosses) >= 4:
            break
    if glosses:
        return "; ".join(glosses[:4])

    # No italics survived: fall back to the running prose of the first sense.
    sense = senses[0]
    parts = [sense.text or ""]
    for child in sense:
        if id(child) not in skip and child.tag not in DROP:
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    txt = clean("".join(parts))
    txt = re.split(r"(?<=[a-z])[.;:](?=\s|$)", txt)[0]
    txt = clean(txt)
    # The prose runs the apparatus and the meanings together — "partt.; to be",
    # "comp.; better; sup.; best" — so weed it out clause by clause.
    txt = "; ".join(c for c in (clean(p) for p in txt.split(";"))
                    if c and not apparatus(c) and not cross_reference(c))
    if len(txt) > 160:
        txt = txt[:157].rsplit(" ", 1)[0] + "…"
    return txt if len(txt) >= 4 and ENGLISH_OK.match(txt) else None


def load(ls_dir, matcher):
    for path in sorted(glob.glob(os.path.join(ls_dir, "*.xml"))):
        data = open(path, encoding="utf-8").read()
        for m in ENTRY_RE.finditer(data):
            block = m.group(0)
            km = KEY_RE.search(block)
            if not km:
                continue
            key = km.group(1)
            if not key or not matcher.interesting(key):
                continue
            g = gloss_from_entry(block, key)
            if g:
                matcher.add(key, [g])

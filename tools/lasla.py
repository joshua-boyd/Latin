#!/usr/bin/env python3
"""Turn LASLA's CoNLL-U Plus files into the per-book JSON the reader loads.

LASLA differs from the Perseus treebank in four ways that shape everything
here:

*no syntax*      HEAD and DEPREL are "_" throughout. There is no dependency
                 annotation, so the reader's Function row has nothing to show
                 for these texts and is hidden.

*real citations* Every token carries CitationHierarchy=Liber_1,Capitulum_1,
                 Paragraphus_1. That is a canonical reference you can look up
                 in any edition — a real gain over Perseus, whose Tacitus file
                 has no citations at all.

*UD features*    Morphology is UD FEATS, not a nine-character ALDT tag. Latin
                 tense is Tense x Aspect there: the perfect is Past+Perf, the
                 imperfect Past+Imp. The rendering is done here rather than in
                 the browser so the mapping lives next to the data it
                 describes; the reader prints the result verbatim.

*no punctuation* LASLA lemmatises words only. There are no PUNCT tokens, so
                 the text displays unpunctuated.
"""

import collections
import os
import re

CITE_RE = re.compile(r"CitationHierarchy=([^|\t\n]+)")

# UPOS -> what to call it in the popup
POS = {
    "NOUN": "noun", "PROPN": "proper noun", "VERB": "verb", "AUX": "verb",
    "ADJ": "adjective", "ADV": "adverb", "ADP": "preposition",
    "CCONJ": "conjunction", "SCONJ": "subordinating conjunction",
    "PRON": "pronoun", "DET": "determiner", "NUM": "numeral",
    "PART": "particle", "INTJ": "interjection", "PUNCT": "punctuation",
    "X": "unclassified",
}

# Latin tense is Tense x Aspect. Non-finite forms carry Aspect alone.
TENSE = {
    ("Pres", "Imp"): "present",
    ("Past", "Imp"): "imperfect",
    ("Past", "Perf"): "perfect",
    ("Pqp", "Perf"): "pluperfect",
    ("Fut", "Imp"): "future",
    ("Fut", "Perf"): "future perfect",
    (None, "Imp"): "present",
    (None, "Perf"): "perfect",
    (None, "Prosp"): "future",
}

MOOD = {"Ind": "indicative", "Sub": "subjunctive", "Imp": "imperative"}
VERBFORM = {"Inf": "infinitive", "Part": "participle", "Ger": "gerund",
            "Gdv": "gerundive", "Sup": "supine"}
VOICE = {"Act": "active", "Pass": "passive"}
CASE = {"Nom": "nominative", "Gen": "genitive", "Dat": "dative",
        "Acc": "accusative", "Abl": "ablative", "Voc": "vocative",
        "Loc": "locative"}
GENDER = {"Masc": "masculine", "Fem": "feminine", "Neut": "neuter"}
NUMBER = {"Sing": "singular", "Plur": "plural", "Plural": "plural"}
# UD 2.11 renamed the Latin superlative from Sup to Abs.
DEGREE = {"Cmp": "comparative", "Abs": "superlative", "Sup": "superlative"}
PRONTYPE = {"Rel": "relative", "Dem": "demonstrative", "Int": "interrogative",
            "Ind": "indefinite", "Tot": "universal", "Neg": "negative",
            "Emp": "emphatic", "Con": "correlative"}
NUMTYPE = {"Card": "cardinal", "Ord": "ordinal", "Dist": "distributive",
           "Mult": "multiplicative"}


def gender_of(raw):
    """Underspecified forms carry several genders ('Fem,Masc'); say so, unless
    the form is ambiguous between all three, where it tells you nothing."""
    if not raw:
        return ""
    parts = raw.split(",")
    if len(parts) >= 3:
        return ""
    return " or ".join(GENDER.get(p, p) for p in parts)


def parse_of(upos, feats):
    """Render one token's morphology the way a grammar would say it."""
    if upos == "_" and not feats:
        return "not annotated"
    d = dict(x.split("=", 1) for x in feats.split("|") if "=" in x) if feats != "_" else {}

    pos = POS.get(upos, "word")
    verbform = d.get("VerbForm")
    mood = MOOD.get(d.get("Mood", ""), "")
    tense = TENSE.get((d.get("Tense"), d.get("Aspect")), "")
    voice = VOICE.get(d.get("Voice", ""), "")
    person = d.get("Person")
    number = NUMBER.get(d.get("Number", ""), "")
    gender = gender_of(d.get("Gender"))
    case = CASE.get(d.get("Case", ""), "")
    degree = DEGREE.get(d.get("Degree", ""), "")

    nominal = " ".join(x for x in (gender, case, number) if x)
    groups = []

    if verbform == "Part":
        groups.append(" ".join(x for x in (tense, voice, "participle") if x))
        if nominal:
            groups.append(nominal)
    elif verbform in ("Gdv", "Ger", "Sup"):
        groups.append(VERBFORM[verbform])
        if case:
            groups.append(case)
    elif verbform == "Inf":
        groups.append(" ".join(x for x in (tense, voice, "infinitive") if x))
    elif mood:
        groups.append(" ".join(x for x in (tense, voice, mood) if x))
        agree = " ".join(x for x in (
            "%s person" % {"1": "1st", "2": "2nd", "3": "3rd"}.get(person, person or ""),
            number) if x.strip())
        if agree.strip():
            groups.append(agree)
    elif nominal:
        groups.append(nominal)

    if degree:
        groups.append(degree)
    if d.get("Reflex") == "Yes":
        groups.append("reflexive")
    if d.get("Poss") == "Yes":
        groups.append("possessive")
    if d.get("Polarity") == "Neg":
        groups.append("negative")
    if upos in ("PRON", "DET") and d.get("PronType") in PRONTYPE:
        groups.append(PRONTYPE[d["PronType"]])
    if upos == "NUM" and d.get("NumType") in NUMTYPE:
        groups.append(NUMTYPE[d["NumType"]])
    if d.get("Abbr") == "Yes":
        groups.append("abbreviated")

    return pos + " — " + ", ".join(groups) if groups else pos


class Table:
    """Interns repeated strings so each token can store small integer ids."""

    def __init__(self):
        self.items = []
        self._map = {}

    def idx(self, val):
        if val not in self._map:
            self._map[val] = len(self.items)
            self.items.append(val)
        return self._map[val]


def cite_of(misc):
    m = CITE_RE.search(misc)
    if not m:
        return None
    d = dict(x.split("_", 1) for x in m.group(1).split(",") if "_" in x)
    return d.get("Liber"), d.get("Capitulum"), d.get("Paragraphus")


def read(path):
    """Yield (liber, unit_label, token dict) for every word in a file.

    unit_label is "chapter.section" where the text has both levels and plain
    "section" where it has only one — Cicero's speeches are cited by section
    alone, Caesar and Tacitus by chapter and section.
    """
    sid = 0
    for line in open(path, encoding="utf-8"):
        if line.startswith("# sent_id"):
            sid += 1
            continue
        if not line[:1].isdigit():
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) < 10 or "-" in f[0] or "." in f[0]:
            continue  # multiword ranges and empty nodes
        cite = cite_of(f[9])
        if not cite:
            continue
        liber, cap, par = cite
        unit = ".".join(x for x in (cap, par) if x)
        if not unit:
            continue
        yield (int(liber) if liber and liber.isdigit() else 1), unit, {
            "form": f[1],
            "lemma": f[2] if f[2] != "_" else "",
            "upos": f[3],
            "parse": parse_of(f[3], f[5]),
            "sid": sid,
        }


def build(path, out_dir, book_no=None):
    """One .conllup -> one JSON per liber. Returns a list of division records."""
    books = collections.OrderedDict()
    for liber, unit, tok in read(path):
        books.setdefault(liber, collections.OrderedDict()).setdefault(unit, []).append(tok)

    divisions = []
    for liber, units in books.items():
        n = book_no if book_no is not None else liber
        lemmas, parses = Table(), Table()
        lines, total = [], 0
        for unit, toks in units.items():
            packed = [[t["form"], lemmas.idx(t["lemma"]), parses.idx(t["parse"]),
                       1 if t["upos"] == "PROPN" else 0, t["sid"]] for t in toks]
            lines.append({"n": unit, "w": packed})
            total += len(packed)

        os.makedirs(out_dir, exist_ok=True)
        data = {"book": n, "scheme": "ud", "lemmas": lemmas.items,
                "parses": parses.items, "lines": lines}
        with open(os.path.join(out_dir, "book-%d.json" % n), "w",
                  encoding="utf-8") as fh:
            import json
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        divisions.append({"n": n, "units": len(lines), "tokens": total,
                          "first": lines[0]["n"] if lines else "1"})
    return divisions

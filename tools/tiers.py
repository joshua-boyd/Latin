"""Shared fuzzy-matching tiers for lining lexicon headwords up with treebank lemmas.

Perseus lemmas, Lewis & Short headwords and Wiktionary headwords are all Latin
in the Latin alphabet, so they look closer than their Greek counterparts — but
they still disagree in three predictable ways:

*homograph digits*  Morpheus numbers ambiguous lemmas ("sum1", "opus1",
                    "quo1"); L&S numbers a different, overlapping set
                    ("abdico1"/"abdico2" but a bare "opus", "quo").

*i/j and u/v*       L&S prints consonantal i and u as j and v ("jacio",
                    "vt"→"ut" is settled, but "Julius"/"Iulius" is not);
                    Wiktionary standardises on i and u.

*vowel quantity*    L&S marks every headword ("ăb, ā"), the treebank marks
                    none. The key attribute is usually unmarked, but not
                    always.

So we try progressively looser keys and take the first that hits.
"""

import re
import unicodedata

# combining macron, breve, diaeresis, acute — quantity and stress marks that
# the dictionaries print and the treebank does not
QUANTITY = dict.fromkeys([0x0304, 0x0306, 0x0308, 0x0301, 0x0300])

TRAILING_DIGITS = re.compile(r"\d+$")
EDGE_JUNK = re.compile(r"^[-\s†*]+|[-\s†*]+$")


def _nfd(s):
    return unicodedata.normalize("NFD", s)


def _nfc(s):
    return unicodedata.normalize("NFC", s)


def norm_lemma(raw):
    """Clean up annotation noise in a treebank lemma.

    Enclitics are lemmatised with a leading hyphen ("-que", "-ve1") and a
    handful of tokens carry an editorial dagger; neither belongs in a lookup
    key, but both must survive in the lemma we display.
    """
    return EDGE_JUNK.sub("", _nfc(raw.strip()))


def k_exact(s):
    """Quantity marks dropped; case, spelling and homograph digit kept."""
    return _nfc(_nfd(EDGE_JUNK.sub("", s)).translate(QUANTITY))


def k_nodigit(s):
    """As above, without the homograph digit the two sides number differently."""
    return TRAILING_DIGITS.sub("", k_exact(s))


def k_loose(s):
    """Case-, i/j- and u/v-insensitive: 'Julius', 'iulius' and 'Iulius' agree."""
    return k_nodigit(s).lower().replace("j", "i").replace("v", "u")


# The editions the treebank follows keep the archaic unassimilated prefixes —
# "conloco", "adservo", "inpero" — where the dictionaries file the assimilated
# spelling. Folding both sides to the assimilated form reconciles them.
ASSIMILATED = [
    ("adc", "acc"), ("adf", "aff"), ("adg", "agg"), ("adl", "all"),
    ("adp", "app"), ("adr", "arr"), ("ads", "ass"), ("adt", "att"),
    ("conl", "coll"), ("conr", "corr"), ("conm", "comm"), ("conp", "comp"),
    ("conb", "comb"), ("inl", "ill"), ("inr", "irr"), ("inm", "imm"),
    ("inp", "imp"), ("obp", "opp"), ("subf", "suff"), ("subp", "supp"),
    # and the one that runs the other way: "expecto" for "exspecto"
    ("exsp", "exp"), ("exst", "ext"),
]


def k_assim(s):
    """k_loose, with prefix assimilation levelled out."""
    k = k_loose(s)
    for old, new in ASSIMILATED:
        if k.startswith(old):
            return new + k[len(old):]
    return k


NAMES = ("exact", "nodigit", "loose", "assim")
FUNCS = (k_exact, k_nodigit, k_loose, k_assim)


class Matcher:
    """Collects glosses under every key tier, then resolves a lemma to the best hit."""

    def __init__(self, lemmas, limit=3):
        self.limit = limit
        self.wanted = {n: {f(l) for l in lemmas} for n, f in zip(NAMES, FUNCS)}
        self.tables = {n: {} for n in NAMES}

    def interesting(self, headword):
        """True if this headword could match something we are looking for."""
        return any(f(headword) in self.wanted[n] for n, f in zip(NAMES, FUNCS))

    def add(self, headword, glosses):
        for name, keyfn in zip(NAMES, FUNCS):
            key = keyfn(headword)
            if key not in self.wanted[name]:
                continue
            bucket = self.tables[name].setdefault(key, [])
            for g in glosses:
                if g not in bucket and len(bucket) < self.limit:
                    bucket.append(g)

    def get(self, lemma):
        for name, keyfn in zip(NAMES, FUNCS):
            hit = self.tables[name].get(keyfn(lemma))
            if hit:
                return hit
        return None

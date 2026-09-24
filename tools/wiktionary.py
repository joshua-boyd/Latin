"""Extract short English glosses for Latin lemmas from a kaikki.org dump."""

import json
import re

FORM_OF = re.compile(
    r"^(inflection|inflected form|form|alternative form|alternative spelling|"
    r"misspelling|abbreviation|contraction|obsolete form|syncopated form|"
    r"nominative|genitive|dative|accusative|ablative|vocative|locative|"
    r"first|second|third|singular|plural|"
    r"present|imperfect|perfect|pluperfect|future|"
    r"masculine|feminine|neuter|comparative|superlative|"
    r"verbal noun|supine|gerund|gerundive|participle)\b.*\bof\b",
    re.I,
)
PAREN_ONLY = re.compile(r"^\(.*\)$")
LEADING_LABEL = re.compile(r"^\((?:[^()]*)\)\s*")

# Enclitic -que, -ve and -ne are separate tokens in the treebank, so unlike the
# Greek build we keep Wiktionary's suffix entries.
SKIP_POS = {"prefix", "infix", "interfix", "phrase", "proverb",
            "character", "punct", "romanization", "abbrev"}

# This is a reader for classical prose, so a sense the dictionary marks as
# later Latin is a last resort: Wiktionary's Gallia is Gaul first and France
# third, and taking them in order would gloss Caesar with modern geography.
LATER_LATIN = {"New-Latin", "Medieval-Latin", "Late-Latin",
               "Ecclesiastical-Latin", "Vulgar-Latin", "Renaissance-Latin"}

# Wiktionary splits some entries into a lead-in and its sub-senses, and the
# flattened dump keeps only the lead-in: "A Roman cognomen — famously held by",
# "especially:". Both end mid-thought, and neither is a definition.
DANGLING = re.compile(
    r"\b(by|of|to|with|for|from|as|in|on|and|or|the|an?|that|such)$", re.I)
LEAD_IN = {"especially", "namely", "specifically", "in particular", "chiefly"}

MAX_LEN = 140


def tidy(raw):
    """One raw Wiktionary gloss -> a short definition, or None."""
    g = re.sub(r"\s+", " ", raw).strip()
    g = LEADING_LABEL.sub("", g)  # drop "(poetic)" style prefixes
    g = g.rstrip(" .:")  # glosses get joined with "; "
    # A gloss-in-parentheses is encyclopaedia, not definition, and dropping it
    # is what keeps long entries from being discarded whole: Gallia's
    # "Gaul (a historical region of Western Europe … (Lombardy) …)" becomes
    # "Gaul". Cutting at the bracket beats matching it — the asides nest.
    if len(g) > MAX_LEN and " (" in g:
        g = g.split(" (", 1)[0].rstrip(" .:,;")
    if not g or len(g) > MAX_LEN or len(g) < 2:
        return None
    if FORM_OF.match(g) or PAREN_ONLY.match(g):
        return None
    if DANGLING.search(g) or g.lower() in LEAD_IN:
        return None
    return g


def collect(senses, glosses):
    """Add each sense's glosses, skipping ones already covered."""
    for sense in senses:
        tags = sense.get("tags") or []
        if "form-of" in tags or "alt-of" in tags:
            continue
        for raw in sense.get("glosses") or []:
            g = tidy(raw)
            if not g:
                continue
            # The lead-in and its sub-sense often survive as near-duplicates;
            # keep the longer of the two.
            dup = next((h for h in glosses
                        if h.lower().startswith(g.lower())
                        or g.lower().startswith(h.lower())), None)
            if dup is None:
                glosses.append(g)
            elif len(g) > len(dup):
                glosses[glosses.index(dup)] = g
        if len(glosses) >= 3:
            return


def load(path, matcher):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            word = d.get("word")
            if not word or d.get("pos") in SKIP_POS:
                continue
            if not matcher.interesting(word):
                continue
            senses = d.get("senses", [])
            classical = [s for s in senses
                         if not LATER_LATIN.intersection(s.get("tags") or [])]
            glosses = []
            collect(classical, glosses)
            if not glosses:
                collect(senses, glosses)
            if glosses:
                matcher.add(word, glosses[:3])

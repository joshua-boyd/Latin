#!/usr/bin/env python3
"""Regenerate everything under data/ from the upstream sources.

    python3 tools/build.py            # download what's missing, then build
    python3 tools/build.py --offline  # build from an already-populated cache

Downloads land in tools/cache/ (about 1.4 GB) and are not committed; only the
generated JSON under data/ is.

To add another treebanked text, append an entry to WORKS. A *sectioned* work
is one file addressed by book-or-speech and chapter; a *prose* work has no
citations at all and is numbered by sentence; a *verse* work is one poem split
into books by line citation. Everything else — the JSON, the shared lexicon
and the site's pickers — follows from that list.
"""

import glob
import json
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_text

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(ROOT, "data")

TREEBANK_URL = ("https://raw.githubusercontent.com/PerseusDL/treebank_data/master/"
                "v2.1/Latin/texts/%s.tb.xml")
# Perseus ships two copies of Lewis & Short; -eng2 is the same dictionary with
# tidier markup and real Unicode Greek, so one file is all we need.
LS_URL = ("https://raw.githubusercontent.com/PerseusDL/lexica/master/"
          "CTS_XML_TEI/perseus/pdllex/lat/ls/lat.ls.perseus-eng2.xml")
WIKT_URL = "https://kaikki.org/dictionary/Latin/kaikki.org-dictionary-Latin.jsonl"

WORKS = [
    {
        "id": "caesar",
        "title": "Caesar",
        "author": "C. Iulius Caesar",
        "label": "Gallic War",
        "latin": "Bellum Gallicum",
        "ref": "Caes. Gal.",
        "kind": "sectioned",
        "unit": "chapter",
        "noun": "Book",
        "source": "phi0448.phi001.perseus-lat1",
        "titles": {2: "The Campaign against the Belgae"},
        "note": ("Of the Gallic War the treebank annotates twelve chapters of "
                 "Book 2; the chapters it skips are simply absent."),
    },
    {
        "id": "cicero",
        "title": "Cicero",
        "author": "M. Tullius Cicero",
        "label": "Against Catiline",
        "latin": "In Catilinam",
        "ref": "Cic. Catil.",
        "kind": "sectioned",
        "unit": "chapter",
        "noun": "Oration",
        "source": "phi0474.phi013.perseus-lat1",
        "titles": {1: "Delivered in the Senate", 2: "Delivered to the People"},
        "note": ("Numbered by chapter, the unit the annotators recorded, not by "
                 "the finer section numbers also used to cite these speeches. "
                 "The First Catilinarian is complete; the Second breaks off in "
                 "chapter 11, and chapter 9 was never annotated."),
    },
    {
        "id": "tacitus",
        "title": "Tacitus",
        "author": "Cornelius Tacitus",
        "label": "Histories",
        "latin": "Historiae",
        "ref": "Tac. Hist.",
        # No cite, no subdoc — the sentence is the finest unit we can honestly
        # number by, exactly as with Lysias in the Greek reader.
        "kind": "prose",
        "unit": "sentence",
        "noun": "Book",
        "parts": [
            {"n": 1, "source": "phi1351.phi005.perseus-lat1",
             "title": "The Year of the Four Emperors begins"},
        ],
        "note": ("The treebank records no chapter or section numbers for this "
                 "text, so it is numbered by sentence. Upstream the file is "
                 "filed under Tacitus's Annals; its text is in fact the opening "
                 "of the Histories."),
    },
]


def cache_path(urn):
    return os.path.join(CACHE, urn.split(".perseus")[0] + ".tb.xml")


def sources_of(work):
    if work["kind"] == "prose":
        return [p["source"] for p in work["parts"]]
    return [work["source"]]


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("downloading", os.path.basename(dest), flush=True)
    tmp = dest + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, dest)


def main():
    offline = "--offline" in sys.argv
    wikt = os.path.join(CACHE, "wiktionary-lat.jsonl")
    ls_dir = os.path.join(CACHE, "ls")

    if not offline:
        for work in WORKS:
            for urn in sources_of(work):
                fetch(TREEBANK_URL % urn, cache_path(urn))
        fetch(WIKT_URL, wikt)
        fetch(LS_URL, os.path.join(ls_dir, "ls02.xml"))

    needed = [wikt, ls_dir]
    for work in WORKS:
        needed += [cache_path(u) for u in sources_of(work)]
    for path in needed:
        if not os.path.exists(path):
            sys.exit("missing source: %s (run without --offline)" % path)

    index = []
    for work in WORKS:
        out = os.path.join(DATA, work["id"])
        print("\n--- %s, %s ---" % (work["title"], work["label"]), flush=True)
        titles = dict(work.get("titles") or {})
        if work["kind"] == "prose":
            divisions = []
            for part in work["parts"]:
                divisions += build_text.build_prose(
                    cache_path(part["source"]), out, part["n"])
                titles[part["n"]] = part.get("title")
        elif work["kind"] == "verse":
            divisions = build_text.build_verse(cache_path(work["source"]), out)
        else:
            divisions = build_text.build_sectioned(cache_path(work["source"]), out)

        entry = {k: work[k] for k in
                 ("id", "title", "author", "label", "latin", "ref", "kind", "unit", "noun")}
        if work.get("note"):
            entry["note"] = work["note"]
        entry["divisions"] = [
            {"n": d["n"], "units": d["units"], "first": d["present"][0],
             **({"title": titles[d["n"]]} if titles.get(d["n"]) else {})}
            for d in divisions
        ]
        index.append(entry)

    # One lexicon serves every work, so feed it the union of their lemmas.
    # Punctuation is lemmatised too ("comma1", "PERIOD1", a bare "?"), but the
    # reader never makes it clickable, so leave it out rather than let it
    # depress a coverage figure no reader will ever notice.
    lemmas = set()
    for path in glob.glob(os.path.join(DATA, "*", "book-*.json")):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        for line in d["lines"]:
            for w in line["w"]:
                tag = d["postags"][w[2]]
                if d["lemmas"][w[1]] and not tag.startswith("u"):
                    lemmas.add(d["lemmas"][w[1]])
    union = os.path.join(DATA, "lemmas.txt")
    with open(union, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(lemmas)))
    print("\n--- lexicon (%d distinct lemmas across %d works) ---"
          % (len(lemmas), len(WORKS)), flush=True)
    subprocess.check_call(
        [sys.executable, os.path.join(HERE, "build_lexicon.py"), union, ls_dir,
         wikt, os.path.join(DATA, "lexicon.json")], cwd=HERE)

    with open(os.path.join(DATA, "works.json"), "w", encoding="utf-8") as fh:
        json.dump({"works": index}, fh, ensure_ascii=False, indent=1)
    print("\ndone — data/ regenerated")


if __name__ == "__main__":
    main()

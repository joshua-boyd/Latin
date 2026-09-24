#!/usr/bin/env python3
"""Turn Perseus treebank XML into the per-division JSON the reader loads.

Three shapes of source, because the Latin treebank is not uniform:

*sectioned*  Caesar and Cicero are addressed by book-or-speech and chapter,
             Caesar with a cite="urn:...:2.5" on every word and Cicero with a
             subdoc="1.7" on every sentence. One file can hold several
             divisions, and the annotators did not always finish a book, so
             the chapters present are not necessarily contiguous.

*prose*      The Tacitus file carries neither cite nor subdoc — every sentence
             has subdoc="" — so canonical numbers simply are not in the data
             and the finest unit available is the sentence.

*verse*      One poem split into books by citation and numbered by line. No
             Caesar, Cicero or Tacitus is verse; this path is here because
             Vergil, Ovid and Propertius sit in the same treebank.

All three produce the same JSON so the reader only needs one code path; the
"unit" field says what the numbers mean.
"""

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET

CITE_RE = re.compile(r":(\d+)\.(\d+)\s*$")
SUBDOC_RE = re.compile(r"^(\d+)\.(\d+)$")


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


def token(word, sid):
    return {
        "id": word.get("id") or "0",
        "form": word.get("form") or "",
        "lemma": word.get("lemma") or "",
        "postag": word.get("postag") or "",
        "rel": word.get("relation") or "",
        "head": word.get("head") or "0",
        "sid": sid,
    }


def real_words(sentence):
    """Annotators insert artificial="elliptic" nodes for words the author omits;
    they carry no text and must not be displayed."""
    return [w for w in sentence.findall("word") if not w.get("artificial")]


def write(out_dir, n, unit, groups):
    """groups: ordered list of (number, [token dicts])."""
    lemmas, postags, rels = Table(), Table(), Table()
    lines = []
    total = 0
    for num, recs in groups:
        packed = []
        for r in recs:
            packed.append([
                r["form"],
                lemmas.idx(r["lemma"]),
                postags.idx(r["postag"]),
                rels.idx(r["rel"]),
                int(r["sid"]),
                int(r["id"]),
                int(r["head"] or 0),
            ])
        lines.append({"n": num, "w": packed})
        total += len(packed)

    os.makedirs(out_dir, exist_ok=True)
    data = {
        "book": n,
        "unit": unit,
        "lemmas": lemmas.items,
        "postags": postags.items,
        "rels": rels.items,
        "lines": lines,
    }
    with open(os.path.join(out_dir, "book-%d.json" % n), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    return {"n": n, "units": len(lines), "tokens": total}


def _fill_gaps(recs):
    """Punctuation has no citation of its own; it inherits the word beside it."""
    last = None
    for r in recs:
        if r["loc"] is None:
            r["loc"] = last
        else:
            last = r["loc"]
    last = None
    for r in reversed(recs):
        if r["loc"] is None:
            r["loc"] = last
        else:
            last = r["loc"]


def _split(books, out_dir, unit, label):
    """Turn {division: [tokens]} into one JSON file per division."""
    divisions = []
    for book in sorted(books):
        recs = sorted(books[book], key=lambda r: (r["loc"][1], r["s"], r["w"]))
        groups, cur_n, cur = [], None, None
        for r in recs:
            if r["loc"][1] != cur_n:
                cur_n, cur = r["loc"][1], []
                groups.append((cur_n, cur))
            cur.append(r)
        info = write(out_dir, book, unit, groups)
        nums = [g[0] for g in groups]
        info["present"] = nums
        divisions.append(info)
        gaps = [x for x in range(nums[0], nums[-1] + 1) if x not in set(nums)]
        print("  %s %2d: %4d %ss (%d-%d%s), %6d tokens"
              % (label, book, info["units"], unit, nums[0], nums[-1],
                 ", %d missing" % len(gaps) if gaps else "", info["tokens"]))
    return divisions


def build_sectioned(src, out_dir):
    """One file -> one JSON per book or speech, numbered by chapter.

    A word's own cite wins where there is one; otherwise the sentence's subdoc
    stands in, inherited from the sentence before when the attribute is blank.
    """
    root = ET.parse(src).getroot()
    books = {}
    dropped = 0
    carried = None
    for s_idx, sentence in enumerate(root.iter("sentence")):
        sid = sentence.get("id") or "0"
        m = SUBDOC_RE.match((sentence.get("subdoc") or "").strip())
        if m:
            carried = (int(m.group(1)), int(m.group(2)))
        sub = carried

        recs = []
        for w_idx, word in enumerate(real_words(sentence)):
            c = CITE_RE.search(word.get("cite") or "")
            rec = token(word, sid)
            rec["loc"] = (int(c.group(1)), int(c.group(2))) if c else sub
            rec["s"], rec["w"] = s_idx, w_idx
            recs.append(rec)

        _fill_gaps(recs)
        for r in recs:
            if r["loc"] is None:
                dropped += 1
            else:
                books.setdefault(r["loc"][0], []).append(r)
    if dropped:
        print("  warning: %d tokens had no resolvable citation" % dropped)
    return _split(books, out_dir, "chapter", "part")


def build_verse(src, out_dir):
    """One poem -> one file per book, numbered by line."""
    root = ET.parse(src).getroot()
    books = {}
    dropped = 0
    for s_idx, sentence in enumerate(root.iter("sentence")):
        sid = sentence.get("id") or "0"
        recs = []
        for w_idx, word in enumerate(real_words(sentence)):
            m = CITE_RE.search(word.get("cite") or "")
            rec = token(word, sid)
            rec["loc"] = (int(m.group(1)), int(m.group(2))) if m else None
            rec["s"], rec["w"] = s_idx, w_idx
            recs.append(rec)

        _fill_gaps(recs)
        for r in recs:
            if r["loc"] is None:
                dropped += 1
            else:
                books.setdefault(r["loc"][0], []).append(r)
    if dropped:
        print("  warning: %d tokens had no resolvable citation" % dropped)
    return _split(books, out_dir, "line", "book")


def build_prose(src, out_dir, n):
    """One uncited work -> one file, numbered by sentence."""
    root = ET.parse(src).getroot()
    groups = []
    for sentence in root.iter("sentence"):
        sid = sentence.get("id") or "0"
        recs = [token(w, sid) for w in real_words(sentence)]
        if recs:
            groups.append((len(groups) + 1, recs))
    info = write(out_dir, n, "sentence", groups)
    info["present"] = [g[0] for g in groups]
    print("  part %2d: %4d sentences, %6d tokens" % (n, info["units"], info["tokens"]))
    return [info]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("sectioned", "prose", "verse"),
                    default="sectioned")
    ap.add_argument("--division", type=int, help="division number (prose only)")
    ap.add_argument("src")
    ap.add_argument("out")
    a = ap.parse_args()
    if a.mode == "prose":
        if a.division is None:
            ap.error("--division is required for prose")
        build_prose(a.src, a.out, a.division)
    elif a.mode == "verse":
        build_verse(a.src, a.out)
    else:
        build_sectioned(a.src, a.out)


if __name__ == "__main__":
    main()

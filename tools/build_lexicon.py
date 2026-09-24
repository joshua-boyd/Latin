#!/usr/bin/env python3
"""Merge Wiktionary and Lewis & Short glosses into one lemma -> definition file.

Wiktionary supplies short modern glosses and covers the proper names L&S
buries in prosopography; L&S fills in the rarer vocabulary and the technical
military and legal words Wiktionary lacks.
"""

import json
import sys

import lewis_short
import tiers
import wiktionary

LEMMA_FILE, LS_DIR, WIKT_FILE, OUT_FILE = sys.argv[1:5]


STUBS = {"masc", "fem", "neut", "sq", "pl", "sg", "adj", "adv", "v", "cf",
         "dim", "name", "nom", "gen", "dat", "acc", "abl", "voc", "loc", "prop"}


def solid(text):
    """Reject leftovers like a bare 'fem' from a cross-reference-only entry."""
    t = text.strip().strip(".").lower()
    return len(t) > 2 and t not in STUBS


def main():
    raw_lemmas = [l.strip() for l in open(LEMMA_FILE, encoding="utf-8") if l.strip()]
    keyed = {l: tiers.norm_lemma(l) for l in raw_lemmas}
    targets = sorted(set(v for v in keyed.values() if v))

    wikt = tiers.Matcher(targets)
    print("scanning Wiktionary…", flush=True)
    wiktionary.load(WIKT_FILE, wikt)

    ls = tiers.Matcher(targets, limit=2)
    print("scanning Lewis & Short…", flush=True)
    lewis_short.load(LS_DIR, ls)

    out = {}
    stats = {"both": 0, "wikt only": 0, "l&s only": 0, "miss": 0}
    misses = []
    for raw, key in sorted(keyed.items()):
        w = [g for g in (wikt.get(key) or []) if solid(g)] if key else []
        l = [g for g in (ls.get(key) or []) if solid(g)] if key else []
        if w and l:
            stats["both"] += 1
        elif w:
            stats["wikt only"] += 1
        elif l:
            stats["l&s only"] += 1
        else:
            stats["miss"] += 1
            misses.append(raw)
            continue
        # Wiktionary wins when both have the lemma: its glosses are short, and
        # L&S spends its first sense on etymology and quantity often enough
        # that its opening italics are a worse one-line answer.
        if w:
            out[raw] = ["; ".join(w[:3]), 0]
        else:
            out[raw] = [" | ".join(l[:2]), 1]

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with open(OUT_FILE + ".misses.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(misses))
    print(stats, "coverage %.1f%%" % (100.0 * len(out) / max(1, len(keyed))))


if __name__ == "__main__":
    main()

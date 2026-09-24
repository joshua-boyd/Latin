#!/usr/bin/env python3
"""Machine-annotate De Re Publica and De Legibus with LatinCy.

Neither work appears in LASLA or in any dependency treebank, so their
morphology has to be generated rather than looked up. This runs the LatinCy
`la_core_web_lg` pipeline over the extracted text and writes CoNLL-U Plus
files into tools/cache/auto/, in the same shape LASLA ships — same columns,
same CitationHierarchy in MISC — so tools/lasla.py reads them unchanged and
the rest of the build does not need to know the difference.

It needs spaCy and a ~500 MB model, which the main build has no other use for,
so it runs from its own virtualenv and caches its output. build.py calls it
only when the cached files are missing:

    python3 -m venv tools/cache/venv
    tools/cache/venv/bin/pip install spacy==3.8.16
    tools/cache/venv/bin/pip install \\
      https://huggingface.co/latincy/la_core_web_lg/resolve/main/la_core_web_lg-3.9.8-py3-none-any.whl
    tools/cache/venv/bin/python tools/annotate.py

The morphology this produces is *not* hand-checked. The reader labels these
two works accordingly.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_text

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache", "auto")

MODEL = "la_core_web_lg"

WORKS = [
    ("Cicero_DeRePublica", lambda: auto_text.de_re_publica(
        os.path.join(CACHE, "derepublica.xml"))),
    ("Cicero_DeLegibus", lambda: auto_text.de_legibus(
        [os.path.join(CACHE, "leg%d.html" % n) for n in (1, 2, 3)])),
]

COLUMNS = ("# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL "
           "DEPS MISC\n")


def rows_for(nlp, sections):
    """{book: [(section, [conllu row, ...]), ...]}"""
    books = {}
    texts = [t for _, _, t in sections]
    for (book, sec, _), doc in zip(sections, nlp.pipe(texts, batch_size=32)):
        misc = "CitationHierarchy=Liber_%s,Paragraphus_%s" % (book, sec)
        rows, i = [], 0
        for tok in doc:
            if tok.is_space:
                continue
            i += 1
            feats = str(tok.morph) or "_"
            rows.append("\t".join([
                str(i), tok.text, tok.lemma_ or "_", tok.pos_ or "X",
                tok.tag_ or "_", feats, "_", "_", "_", misc]))
        if rows:
            books.setdefault(book, []).append((sec, rows))
    return books


def main():
    import spacy
    print("loading %s…" % MODEL, flush=True)
    nlp = spacy.load(MODEL)
    # The parser and NER cost time and we keep neither: LASLA has no syntax,
    # so the reader shows none, and nothing downstream reads entities.
    for pipe in ("parser", "ner"):
        if pipe in nlp.pipe_names:
            nlp.disable_pipe(pipe)

    for stem, load in WORKS:
        sections = load()
        books = rows_for(nlp, sections)
        for book, units in sorted(books.items()):
            path = os.path.join(CACHE, "%s_%s%d.conllup" % (stem, stem.split("_")[1], book))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(COLUMNS)
                for sec, rows in units:
                    fh.write("# sent_id = %s-%s-%s\n" % (stem, book, sec))
                    fh.write("\n".join(rows))
                    fh.write("\n\n")
            print("  %s: %d sections, %d tokens"
                  % (os.path.basename(path), len(units),
                     sum(len(r) for _, r in units)), flush=True)


if __name__ == "__main__":
    main()

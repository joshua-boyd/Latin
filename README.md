# Latin Reader

A static website for reading Caesar, Cicero and Tacitus in Latin — all three
complete. Pick a work and a book from the sidebar, then click any word to see
its dictionary form, a full morphological parse and an English definition. The
popup stays open until you click somewhere else.

This is the Latin counterpart of the [Greek reader](https://github.com/joshua-boyd/Greek),
though it reads a different corpus; see *Where the text comes from* below.

## How the annotations work

Every token is addressed **by its position in the text**, not by its spelling.
Each word in `data/<work>/book-N.json` is a separate record carrying its own
lemma and morphology, exactly as the LASLA annotators assigned them at that
spot. Two identically spelled words therefore never share an analysis —
ambiguous forms like `cum`, `quo` or `sua` each get whatever was annotated in
that specific place.

The only thing looked up by key is the English definition, which is keyed on
the lemma the annotators already chose for that token.

## Coverage

| Author | Works | Books | Words |
| --- | --- | --- | --- |
| Caesar | 2 | 10 | 79,039 |
| Cicero | 39 | 63 | 474,079 |
| Tacitus | 5 | 20 | 165,251 |
| **Total** | **46** | **93** | **718,369** |

Caesar is the *Gallic War* and the *Civil War*. Cicero is the speeches and the
three short philosophical works LASLA has lemmatised — the Catilinarians, the
Verrines, the Philippics, *Pro Milone*, *Pro Caelio*, *De Officiis* and the
rest. Tacitus is the *Annals*, the *Histories*, the *Germania*, the *Agricola*
and the *Dialogus*. The *Annals* is missing Books 7–10 because they do not
survive.

All 46 works share one lexicon, covering 87.4% of 12,953 distinct lemmas. Of
the 1,629 gaps, 849 are proper names — the Gallic tribes, Sicilian towns and
minor senators that neither dictionary lists — and the reader labels those as
names using the corpus's own part-of-speech tag rather than guessing from
capitalisation.

## Where the text comes from

The **LASLA** *Opera Latina* corpus, built at the Université de Liège and
published by CIRCSE in Milan as part of the [LiLa](https://lila-erc.eu/)
project. Three consequences are worth knowing before you read:

- **There is no syntax.** LASLA's `HEAD` and `DEPREL` columns are empty
  throughout, so the popup has no "Function" row. It tells you that a word is
  a perfect passive participle in the feminine accusative singular; it does
  not tell you what it modifies.
- **The text is unpunctuated.** LASLA lemmatises words only, so there are no
  punctuation tokens and the page shows continuous text with section numbers
  as the only breaks.
- **Consonantal *v* is written *u*.** `Seruius`, `diuisa`, `uidere`. That is
  the corpus's classical orthography, left as it stands rather than
  normalised, since `u` and `v` cannot be told apart reliably after the fact.

In exchange, every token carries a real citation. LASLA records
`Liber / Capitulum / Paragraphus`, so `Tac. Ann. 1.1.1` in the popup is a
canonical reference you can look up in any edition. Caesar and Tacitus are
numbered book, chapter and section; Cicero's speeches by section alone, which
is how they are cited.

### The Perseus treebank

The site was first built on the [Perseus Latin Dependency
Treebank](https://github.com/PerseusDL/treebank_data), which *does* carry
manual dependency annotation. It covers twelve chapters of *Gallic War* 2, the
First Catilinarian and part of the Second, and the opening of *Histories* 1 —
11,527 words against LASLA's 718,369. `tools/build_text.py` still reads it and
is kept for reference, but it is no longer wired into `tools/build.py`, and
the reader no longer renders its dependency labels.

## Adding another author

Add a table to `tools/lasla_works.py` giving each work an id, a Latin title,
an English one and a citation abbreviation, then list the author in `AUTHORS`
and rerun the build. Books and section numbers come from the data's own
citation hierarchy, so nothing else needs saying. LASLA has Seneca, Pliny,
Ovid, Vergil, Sallust, Plautus, Lucretius, Horace and a dozen more sitting in
the same repository.

## URLs

`#caesar-gallicum.1.20.3` links to a work, book, chapter and section;
`#cicero-archia.1.12` works the same way for a one-book speech numbered
straight through.

## Running it locally

It is a plain static site — no build step, no dependencies:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Publishing to GitHub Pages

Push this directory to a GitHub repository, then in **Settings → Pages** choose
*Deploy from a branch*, branch `main`, folder `/ (root)`. The `.nojekyll` file
keeps Pages from reprocessing the site.

## Regenerating the data

`data/` is committed, so you only need this if you want to rebuild or extend it:

```bash
python3 tools/build.py
```

This downloads the sources into `tools/cache/` (about 1.6 GB, ignored by git)
and regenerates `data/`. Use `--offline` to rebuild from an existing cache.

| Script | Purpose |
| --- | --- |
| `tools/build.py` | Fetches sources and drives the whole build |
| `tools/lasla_works.py` | The work list: ids, titles and citation abbreviations |
| `tools/lasla.py` | CoNLL-U Plus → one JSON file per book, morphology rendered |
| `tools/build_lexicon.py` | Merges both dictionaries into `data/lexicon.json` |
| `tools/lewis_short.py` | Pulls glosses out of Lewis & Short's TEI markup |
| `tools/wiktionary.py` | Pulls glosses out of the Wiktionary dump |
| `tools/tiers.py` | Tolerant headword matching across the three sources |
| `tools/build_text.py` | Perseus treebank XML → JSON (kept, not wired up) |

### Notes on the build

- Latin tense in Universal Dependencies is `Tense` × `Aspect`: the perfect is
  `Past`+`Perf`, the imperfect `Past`+`Imp`, and participles carry `Aspect`
  alone. `tools/lasla.py` renders the morphology at build time rather than in
  the browser so the mapping sits next to the data it describes.
- Underspecified forms carry several genders (`Fem,Masc`). Two are reported as
  "feminine or masculine"; all three is no information, so it is dropped.
- LASLA lemmatises proper nouns in lower case (`roma`, `seruius`). The lexicon
  matches case-insensitively; the popup capitalises them for display.
- Lewis & Short has no `<tr>` elements, so unlike LSJ its glosses have to be
  recovered from the italics inside the first sense — filtering out the
  morphological apparatus (`gen. plur.`, `2d pers. sing.`) that is set in the
  same italics, and the Latin forms, which keep their quantity marks.
- Lemma and headword disagree in predictable ways, so matching falls back
  through four keys: exact → without the homograph digit → i/j and u/v folded
  (which is also what reconciles LASLA's `uideo` with Wiktionary's `video`) →
  prefix assimilation levelled (`conloco` for `colloco`).
- Wiktionary lists senses in historical order, so a sense tagged New or
  Medieval Latin is taken only when there is no classical one. Without that,
  `Gallia` glosses as *France*.
- Wiktionary files participial adjectives and *-e* adverbs (`adiacens`,
  `acute`) as inflected forms. Those senses are held back for a last pass
  rather than dropped, since their glosses are definitions and not pointers.

## Sources and licensing

- Text and morphology: LASLA *Opera Latina*, Université de Liège, via
  [CIRCSE / LiLa](https://github.com/CIRCSE/LASLA) — **CC BY-NC-SA 4.0**
- Definitions: [Wiktionary](https://en.wiktionary.org/) via
  [kaikki.org](https://kaikki.org/) — CC BY-SA 4.0
- Definitions: Lewis & Short, *A Latin Dictionary*, via
  [Perseus](https://github.com/PerseusDL/lexica) — CC BY-SA 3.0

The text and morphology are **NonCommercial**, so the per-work JSON under
`data/<work>/` is released under **CC BY-NC-SA 4.0** and may not be used
commercially. `data/lexicon.json` is built only from Wiktionary and Lewis &
Short and remains **CC BY-SA 4.0**. The site code in `index.html`, `assets/`
and `tools/` is MIT licensed.

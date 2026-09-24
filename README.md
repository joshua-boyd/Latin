# Latin Reader

A static website for reading Caesar's *Gallic War*, Cicero's *Catilinarians*
and Tacitus's *Histories* in Latin. Pick a work and a book from the sidebar,
then click any word to see its dictionary form, a full morphological parse, its
syntactic function and an English definition. The popup stays open until you
click somewhere else.

This is the Latin counterpart of the [Greek reader](https://github.com/joshboyd7/Greek),
built the same way from the same project's treebanks.

## How the annotations work

Every token is addressed **by its position in the text**, not by its spelling.
Each word in `data/<work>/book-N.json` is a separate record carrying its own
lemma, morphology tag and dependency relation, exactly as the Perseus
annotators assigned them at that spot. Two identically spelled words therefore
never share an analysis — ambiguous forms like `cum`, `quo` or `sua` each get
whatever was annotated in that specific place.

The only thing looked up by key is the English definition, which is keyed on
the lemma the annotators already chose for that token.

## Coverage

| Work | Divisions | Units | Tokens |
| --- | --- | --- | --- |
| Caesar, *Gallic War* | Book 2 | 12 chapters | 1,553 |
| Cicero, *In Catilinam* | Orations 1 and 2 | 23 chapters | 6,567 |
| Tacitus, *Histories* | Book 1 | 197 sentences | 3,407 |

All three share one lexicon, covering 98.4% of 2,614 distinct lemmas. The
remaining gaps are almost entirely Gallic tribal names and minor Roman
cognomina, absent from both dictionaries; the reader labels those as names.

### What the treebank actually contains

The Latin Dependency Treebank was annotated text by text, and none of these
three works is annotated whole. That shapes what the site can honestly show:

- **Caesar** is twelve chapters of *Gallic War* Book 2 — 1, 2, 3, 5, 7, 9, 14,
  15, 17, 18, 32 and 33. The chapters in between were never annotated, so they
  are simply not there, and the numbering in the margin skips.
- **Cicero** is the whole of the First Catilinarian and ten chapters of the
  Second, which breaks off at chapter 11 and is missing chapter 9.
- **Tacitus** is roughly the first forty-nine chapters of *Histories* Book 1.

### Chapters, not sections

Caesar's words carry `cite="urn:...:2.5"` and Cicero's sentences carry
`subdoc="1.7"`. Both numbers are **chapters**: the treebank's `1.1` for Cicero
holds 294 words, which is *In Catilinam* 1.1–3, the whole of chapter I. These
speeches are more often cited by the finer section number, so the reader says
"chapter" and means it rather than printing `Cic. Catil. 1.7` and letting it
be read as a section.

### A caveat about Tacitus

The Tacitus file carries no `cite` attributes and gives every sentence an empty
`subdoc`, so canonical numbers are not present in the data at all. Rather than
invent them, the reader numbers it **by sentence** and says so both on the page
and in the popup, which reads `Tac. Hist. 1 · sentence 12` instead of
pretending to be `Tac. Hist. 1.12`.

Upstream the file is filed as `phi1351.phi005`, Tacitus's *Annals*, and its
header says *Annales*. Its text is not the *Annals*: it opens `Initium mihi
operis Servius Galba iterum Titus Vinius consules erunt`, which is *Histories*
1.1. The site labels it by what it is.

## Enclitics

The treebank splits `-que`, `-ve` and `-ne` off as tokens of their own, each
with its own parse and its own dictionary entry. The page sets them flush
against their host so it reads `litterisque` as the manuscript does; the popup
shows `-que` so it is clear what was clicked.

## Adding another text

Append an entry to `WORKS` in `tools/build.py` and rerun the build. A
*sectioned* work is one file addressed by book-or-speech and chapter; a *prose*
work has no citations at all and is numbered by sentence; a *verse* work is one
poem split into books by line citation. The JSON, the shared lexicon and the
site's pickers all follow from that list; no front-end change is needed.
Vergil's *Aeneid*, Ovid's *Metamorphoses*, Sallust, Propertius, Petronius and
Suetonius are all available in the same treebank.

## URLs

`#caesar.2.5` and `#cicero.1.7` link to a work, book and chapter;
`#tacitus.1.12` works the same way for a sentence. A bare `#2.5` still resolves
to Caesar.

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

This downloads the sources into `tools/cache/` (about 1.4 GB, ignored by git)
and regenerates `data/`. Use `--offline` to rebuild from an existing cache.

| Script | Purpose |
| --- | --- |
| `tools/build.py` | Lists the works, fetches sources, drives the whole build |
| `tools/build_text.py` | Treebank XML → one JSON file per book or speech |
| `tools/build_lexicon.py` | Merges both dictionaries into `data/lexicon.json` |
| `tools/lewis_short.py` | Pulls glosses out of Lewis & Short's TEI markup |
| `tools/wiktionary.py` | Pulls glosses out of the Wiktionary dump |
| `tools/tiers.py` | Tolerant headword matching across the three sources |

### Notes on the build

- Nodes marked `artificial="elliptic"` are annotator placeholders for words the
  author omits. They carry no text and are dropped.
- Punctuation has no citation of its own and inherits the chapter of the word
  beside it. It is lemmatised too (`comma1`, `PERIOD1`, a bare `?`), but the
  reader never makes it clickable, so it is left out of the lexicon.
- Lewis & Short has no `<tr>` elements, so unlike LSJ its glosses have to be
  recovered from the italics inside the first sense — filtering out the
  morphological apparatus (`gen. plur.`, `2d pers. sing.`) that is set in the
  same italics, and the Latin forms, which keep their quantity marks.
- Lemma and headword disagree in three predictable ways, so matching falls back
  through four keys: exact → without Morpheus's homograph digit (`opus1` for
  L&S's `opus`) → i/j and u/v folded (`conjuro`, `coniuro`) → prefix
  assimilation levelled (`conloco` for `colloco`, `adservo` for `asservo`).
- Wiktionary lists senses in historical order, so a sense tagged New or
  Medieval Latin is taken only when there is no classical one. Without that,
  `Gallia` glosses as *France*.
- Where both dictionaries have a lemma, Wiktionary wins: its glosses are
  shorter, and L&S spends its first sense on etymology and quantity often
  enough that its opening italics make a worse one-line answer.

## Sources and licensing

- Text and morphology: [Perseus Latin Dependency Treebank](https://github.com/PerseusDL/treebank_data)
  v2.1 — CC BY-SA 3.0
- Definitions: [Wiktionary](https://en.wiktionary.org/) via
  [kaikki.org](https://kaikki.org/) — CC BY-SA 4.0
- Definitions: Lewis & Short, *A Latin Dictionary*, via
  [Perseus](https://github.com/PerseusDL/lexica) — CC BY-SA 3.0

Both dictionary sources are share-alike, so the generated data in `data/` is
released under **CC BY-SA 4.0**. The site code in `index.html`, `assets/` and
`tools/` is MIT licensed.

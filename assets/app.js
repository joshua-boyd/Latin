/* Caesar, Cicero and Tacitus — an annotated reader.
 *
 * Every token rendered here is a distinct record from the Perseus Latin
 * Dependency Treebank, addressed by its position in the text. Nothing is
 * looked up by spelling, so two identically spelled words keep their own
 * separate annotations.
 */
(function () {
  "use strict";

  /* Perseus/ALDT nine-character postag, one slot per feature. The Latin tag
     set differs from the Greek in three places that matter: case has an
     ablative, voice has a deponent, and there is no dual, optative, middle or
     article. A slot the annotators left inapplicable is "-" or "_". */
  var MORPH = [
    { key: "pos", map: {
      n: "noun", v: "verb", t: "participle", a: "adjective", d: "adverb",
      c: "conjunction", r: "preposition", p: "pronoun", m: "numeral",
      i: "interjection", e: "exclamation", g: "particle", u: "punctuation",
      x: "unclassified"
    } },
    { key: "person", map: { 1: "1st person", 2: "2nd person", 3: "3rd person" } },
    { key: "number", map: { s: "singular", p: "plural" } },
    { key: "tense", map: {
      p: "present", i: "imperfect", r: "perfect", l: "pluperfect",
      t: "future perfect", f: "future"
    } },
    { key: "mood", map: {
      i: "indicative", s: "subjunctive", n: "infinitive", m: "imperative",
      p: "participle", d: "gerund", g: "gerundive", u: "supine"
    } },
    { key: "voice", map: {
      a: "active", p: "passive", d: "deponent"
    } },
    { key: "gender", map: { m: "masculine", f: "feminine", n: "neuter" } },
    { key: "case", map: {
      n: "nominative", g: "genitive", d: "dative", a: "accusative",
      b: "ablative", v: "vocative", l: "locative"
    } },
    { key: "degree", map: { c: "comparative", s: "superlative" } }
  ];

  /* ALDT dependency labels. */
  var RELATIONS = {
    PRED: "main verb of the sentence",
    SBJ: "subject",
    OBJ: "object",
    ATR: "modifies a noun",
    ATV: "predicative complement",
    AtvV: "predicative complement",
    PNOM: "predicate noun (with “to be”)",
    OCOMP: "object complement",
    ADV: "adverbial",
    COORD: "coordinating word",
    APOS: "appositive marker",
    AuxP: "preposition",
    AuxC: "subordinating conjunction",
    AuxV: "auxiliary verb",
    AuxR: "reflexive passive",
    AuxX: "comma",
    AuxG: "bracketing punctuation",
    AuxK: "sentence-final punctuation",
    AuxY: "sentence adverbial",
    AuxZ: "emphasising particle",
    ExD: "governing word is omitted",
    nil: "unannotated",
    UNDEFINED: "unannotated"
  };

  var el = {
    text: document.getElementById("text"),
    list: document.getElementById("book-list"),
    works: document.getElementById("work-list"),
    booksHead: document.getElementById("books-head"),
    workName: document.getElementById("work-name"),
    workAuthor: document.getElementById("work-author"),
    popup: document.getElementById("popup"),
    sidebar: document.getElementById("sidebar"),
    reader: document.getElementById("reader"),
    jump: document.getElementById("jump"),
    form: document.getElementById("p-form"),
    ref: document.getElementById("p-ref"),
    gloss: document.getElementById("p-gloss"),
    lemma: document.getElementById("p-lemma"),
    parse: document.getElementById("p-parse"),
    rel: document.getElementById("p-rel"),
    src: document.getElementById("p-src"),
    logeion: document.getElementById("p-logeion")
  };

  var lexicon = null;
  var works = [];           // from data/works.json
  var work = null;          // the work currently selected
  var current = null;       // the division currently rendered
  var tokens = [];          // flat token list for the rendered division
  var activeWord = null;
  var bookCache = {};

  function workById(id) {
    for (var i = 0; i < works.length; i++) {
      if (works[i].id === id) return works[i];
    }
    return null;
  }

  /* Divisions are not always 1..N — the Gallic War here is Book 2 alone. */
  function divisionOf(w, n) {
    for (var i = 0; i < w.divisions.length; i++) {
      if (w.divisions[i].n === n) return w.divisions[i];
    }
    return null;
  }

  function plural(noun) {
    return /s$/.test(noun) ? noun + "es" : noun + "s";
  }

  /* ---------------- data ---------------- */

  function getJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + " → " + r.status);
      return r.json();
    });
  }

  function loadBook(workId, n) {
    var key = workId + ":" + n;
    if (bookCache[key]) return Promise.resolve(bookCache[key]);
    return getJSON("data/" + workId + "/book-" + n + ".json").then(function (d) {
      bookCache[key] = d;
      return d;
    });
  }

  /* ---------------- morphology ---------------- */

  function isPunct(tag) {
    return tag.charAt(0) === "u";
  }

  function feat(tag, slot) {
    var c = tag.charAt(slot);
    if (!c || c === "-" || c === "_") return "";
    return MORPH[slot].map[c] || "";
  }

  var SLOT = { POS: 0, PERSON: 1, NUMBER: 2, TENSE: 3, MOOD: 4, VOICE: 5,
               GENDER: 6, CASE: 7, DEGREE: 8 };

  /* Say it the way a grammar would: "perfect passive participle, masculine
     nominative singular" rather than raw slot order. */
  function parseLine(tag) {
    if (!tag) return "not annotated";

    var pos = feat(tag, SLOT.POS) || "word";
    var mood = feat(tag, SLOT.MOOD);
    var tense = feat(tag, SLOT.TENSE);
    var voice = feat(tag, SLOT.VOICE);
    var person = feat(tag, SLOT.PERSON);
    var number = feat(tag, SLOT.NUMBER);
    var gender = feat(tag, SLOT.GENDER);
    var kase = feat(tag, SLOT.CASE);
    var degree = feat(tag, SLOT.DEGREE);

    var nominal = [gender, kase, number].filter(Boolean).join(" ");
    var groups = [];

    if (mood === "participle" || mood === "gerundive") {
      groups.push([tense, voice, mood].filter(Boolean).join(" "));
      if (nominal) groups.push(nominal);
    } else if (mood === "gerund" || mood === "supine") {
      groups.push(mood);
      if (kase) groups.push(kase);
    } else if (mood === "infinitive") {
      groups.push([tense, voice, "infinitive"].filter(Boolean).join(" "));
    } else if (mood) {
      groups.push([tense, voice, mood].filter(Boolean).join(" "));
      var agree = [person, number].filter(Boolean).join(" ");
      if (agree) groups.push(agree);
    } else if (nominal) {
      groups.push(nominal);
    } else {
      var rest = [tense, voice, person, number].filter(Boolean).join(" ");
      if (rest) groups.push(rest);
    }

    if (degree) groups.push(degree);
    return groups.length ? pos + " — " + groups.join(", ") : pos;
  }

  function relationLabel(rel) {
    if (!rel) return "—";
    var base = rel.replace(/_(CO|AP)$/, "");
    var note = RELATIONS[base] || base;
    if (/_CO$/.test(rel)) note += " (one of two or more coordinated)";
    if (/_AP$/.test(rel)) note += " (part of an appositive)";
    return note + " · " + rel;
  }

  /* ---------------- glosses ---------------- */

  /* Morpheus numbers ambiguous lemmas; the dictionaries mostly do not, and the
     digit is noise on the page. "sum1" reads as "sum". */
  function displayLemma(lemma) {
    return lemma ? lemma.replace(/\d+$/, "") : "";
  }

  /* Roman names run -ius, -ianus and the gentilicial -eius; the treebank
     spells consonantal i as j about as often as not. */
  var GENTILE = /(ius|ianus|inus|eius|ejus|icus)\d*$/i;

  function glossFor(lemma, tag) {
    var hit = lexicon && Object.prototype.hasOwnProperty.call(lexicon, lemma)
      ? lexicon[lemma] : null;
    if (hit) return { text: hit[0], src: hit[1] === 0 ? "Wiktionary" : "Lewis & Short" };

    // Most gaps are the minor Gallic and Roman names neither dictionary lists.
    if (lemma && lemma.charAt(0) !== lemma.charAt(0).toLowerCase()) {
      if (GENTILE.test(lemma)) {
        return { text: "proper name (Roman gentile or derived adjective)",
                 src: null, weak: true };
      }
      return { text: "proper name", src: null, weak: true };
    }
    if (!lemma) return { text: "no dictionary form recorded", src: null, weak: true };
    return { text: "no definition available", src: null, weak: true };
  }

  /* ---------------- rendering ---------------- */

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* The treebank splits enclitics off as their own tokens and marks them with
     a leading hyphen: "litteris" + "-que". They are worth keeping apart —
     -que carries its own parse and its own entry — but the page should read
     "litterisque" as the manuscript does, so the hyphen is dropped from the
     text and kept in the popup, where it identifies what was clicked. */
  function enclitic(form) {
    return form.charAt(0) === "-" && form.length > 1;
  }

  function render(book) {
    current = book;
    tokens = [];

    var div = divisionOf(work, book.book) || {};
    var display = esc(work.latin) + " " + book.book;
    var html = ['<h2 class="book-title"><small>' + esc(work.title) + " · " +
      esc(work.noun) + " " + book.book +
      (div.title ? " · " + esc(div.title) : "") + "</small>" + display + "</h2>"];

    if (work.note) html.push('<div class="prose-note">' + esc(work.note) + "</div>");

    for (var i = 0; i < book.lines.length; i++) {
      var line = book.lines[i];
      var n = line.n;
      var pieces = [];

      for (var j = 0; j < line.w.length; j++) {
        var w = line.w[j];
        var form = w[0];
        var lemma = book.lemmas[w[1]];
        var tag = book.postags[w[2]] || "";
        var rel = book.rels[w[3]] || "";
        var idx = tokens.length;
        tokens.push({ form: form, lemma: lemma, tag: tag, rel: rel, line: n });

        var clipped = enclitic(form);
        var space = pieces.length && !clipped ? " " : "";
        if (isPunct(tag) || (!tag && /^[.,;:!?'"()\[\]—–]+$/.test(form))) {
          pieces.push('<span class="punct">' + esc(form) + "</span>");
        } else {
          var unknown = !lemma ? " unknown" : "";
          pieces.push(
            space +
            '<span class="w' + unknown + (clipped ? " enclitic" : "") +
            '" data-t="' + idx + '">' +
            esc(clipped ? form.slice(1) : form) + "</span>"
          );
        }
      }

      // Every unit here is a paragraph-sized chapter or a whole sentence, so
      // each one is numbered; there is no every-fifth-line convention to keep.
      html.push(
        '<div class="line prose" id="l' + book.book + "-" + n + '">' +
        '<span class="lnum">' + n + "</span>" +
        '<span class="line-text">' + pieces.join("") + "</span>" +
        "</div>"
      );
    }

    el.text.innerHTML = html.join("");
    hidePopup();
  }

  /* ---------------- popup ---------------- */

  function showPopup(span) {
    var t = tokens[+span.dataset.t];
    if (!t) return;

    if (activeWord) activeWord.classList.remove("active");
    activeWord = span;
    span.classList.add("active");

    var g = glossFor(t.lemma, t.tag);

    el.form.textContent = t.form;
    // "Cic. Catil. 1.7" is a real citation; the Tacitus numbers are ours, so
    // say so rather than dress them up as sections.
    el.ref.textContent = current.unit === "sentence"
      ? work.ref + " " + current.book + " · sentence " + t.line
      : work.ref + " " + current.book + "." + t.line;
    el.gloss.textContent = g.text;
    el.gloss.className = "p-gloss" + (g.weak ? " none" : "");
    el.lemma.textContent = displayLemma(t.lemma) || "—";
    el.lemma.className = t.lemma ? "latin-val" : "";
    el.parse.textContent = parseLine(t.tag);
    el.rel.textContent = relationLabel(t.rel);
    el.src.textContent = g.src ? g.src : "";

    if (t.lemma) {
      el.logeion.href = "https://logeion.uchicago.edu/" +
        encodeURIComponent(displayLemma(t.lemma));
      el.logeion.hidden = false;
    } else {
      el.logeion.hidden = true;
    }

    el.popup.hidden = false;
    position(span);
  }

  var GAP = 10;      // space between the word and the popup
  var MARGIN = 8;    // keep this far clear of the viewport edges

  function position(span) {
    var pop = el.popup;
    pop.classList.remove("below");

    // The popup is a child of <body>, so it is placed in document coordinates.
    var sx = window.pageXOffset;
    var sy = window.pageYOffset;
    var word = span.getBoundingClientRect();
    var col = el.text.getBoundingClientRect();
    var bar = document.querySelector(".topbar").getBoundingClientRect().bottom;

    // Pick whichever side of the word has more room, then cap the popup to it
    // so it never runs off a short window.
    var roomAbove = word.top - bar - GAP - MARGIN;
    var roomBelow = window.innerHeight - word.bottom - GAP - MARGIN;
    pop.style.maxHeight = "";
    var natural = pop.offsetHeight;
    var below = natural > roomAbove && roomBelow > roomAbove;
    var room = below ? roomBelow : roomAbove;
    pop.style.maxHeight = Math.max(120, room) + "px";

    var h = pop.offsetHeight;
    var w = pop.offsetWidth;

    // centred on the word, but kept inside the text column and the viewport
    var centre = word.left + word.width / 2;
    var left = centre - w / 2;
    var minLeft = Math.max(MARGIN, Math.min(col.left, window.innerWidth - w - MARGIN));
    var maxLeft = Math.max(minLeft, Math.min(col.right, window.innerWidth - MARGIN) - w);
    if (left < minLeft) left = minLeft;
    if (left > maxLeft) left = maxLeft;

    var top = below ? word.bottom + GAP : word.top - h - GAP;
    pop.classList.toggle("below", below);

    pop.style.left = (left + sx) + "px";
    pop.style.top = (top + sy) + "px";

    // keep the arrow pointing at the word even when the popup was clamped;
    // it would scroll away from the edge once the popup scrolls internally
    pop.classList.toggle("clipped", pop.scrollHeight > pop.clientHeight + 1);
    var arrow = pop.querySelector(".popup-arrow");
    var ax = centre - left - 5.5;
    arrow.style.left = Math.min(Math.max(ax, 12), w - 23) + "px";
  }

  function hidePopup() {
    el.popup.hidden = true;
    if (activeWord) activeWord.classList.remove("active");
    activeWord = null;
  }

  /* ---------------- navigation ---------------- */

  /* Switching work re-lists its divisions, then opens one. */
  function selectWork(id, n, lineNo, push) {
    var next = workById(id) || works[0];
    if (work !== next) {
      work = next;
      el.workAuthor.textContent = work.author;
      el.workName.textContent = work.label || work.title;
      document.title = work.title + " — an annotated Latin reader";
      buildBookList();
      Array.prototype.forEach.call(el.works.querySelectorAll("button"), function (b) {
        var on = b.dataset.work === work.id;
        b.setAttribute("aria-current", String(on));
        b.setAttribute("aria-checked", String(on));
      });
      el.booksHead.textContent = plural(work.noun) + " of " + work.label;
      el.jump.placeholder = "e.g. " + work.divisions[0].n + "." +
        (work.divisions[0].first || 1);
    }
    return selectBook(n || work.divisions[0].n, lineNo, push);
  }

  function selectBook(n, lineNo, push) {
    n = n | 0;
    if (!divisionOf(work, n)) n = work.divisions[0].n;
    el.text.innerHTML = '<p class="loading">Loading ' + esc(work.noun) + " " +
      n + "…</p>";

    Array.prototype.forEach.call(el.list.querySelectorAll("button"), function (b) {
      b.setAttribute("aria-current", String(+b.dataset.book === n));
    });

    return loadBook(work.id, n).then(function (book) {
      render(book);
      if (lineNo) {
        goToLine(n, lineNo);
      } else {
        el.reader.scrollTop = 0;
        window.scrollTo(0, 0);
      }
      if (push !== false) {
        history.replaceState(null, "", hashFor(work.id, n, lineNo));
      }
      el.sidebar.classList.remove("open");
    }).catch(function (e) {
      el.text.innerHTML = '<p class="error">Could not load ' + esc(work.noun) +
        " " + n + ". " + esc(e.message) + "</p>";
    });
  }

  function goToLine(book, line) {
    var target = document.getElementById("l" + book + "-" + line);
    if (!target) return false;
    Array.prototype.forEach.call(el.text.querySelectorAll(".line.target"),
      function (d) { d.classList.remove("target"); });
    target.classList.add("target");
    target.scrollIntoView({ block: "center", behavior: "smooth" });
    return true;
  }

  function parseRef(s) {
    var m = /^\s*(\d{1,2})(?:[.:\s]+(\d{1,4}))?\s*$/.exec(s || "");
    if (!m) return null;
    return { book: +m[1], line: m[2] ? +m[2] : 0 };
  }

  function hashFor(id, book, line) {
    return "#" + id + "." + book + (line ? "." + line : "");
  }

  /* "#cicero.1.7", or a bare "#2.5" meaning the first work. */
  function fromHash() {
    var raw = decodeURIComponent(location.hash.replace(/^#/, ""));
    var m = /^([A-Za-z][A-Za-z0-9_-]*)\.(.+)$/.exec(raw);
    if (m && workById(m[1])) {
      var ref = parseRef(m[2]);
      if (ref) return { id: m[1], book: ref.book, line: ref.line };
    }
    var bare = parseRef(raw);
    if (bare) return { id: works[0].id, book: bare.book, line: bare.line };
    return { id: works[0].id, book: 0, line: 0 };
  }

  /* ---------------- wiring ---------------- */

  function buildWorkList() {
    var html = "";
    for (var i = 0; i < works.length; i++) {
      html += '<li><button type="button" role="radio" aria-checked="false" data-work="' +
        esc(works[i].id) + '">' +
        "<span>" + esc(works[i].title) + "</span>" +
        '<span class="latin">' + esc(works[i].latin) + "</span></button></li>";
    }
    el.works.innerHTML = html;
    el.works.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-work]");
      if (b && b.dataset.work !== work.id) selectWork(b.dataset.work);
    });
  }

  function buildBookList() {
    var html = "";
    for (var i = 0; i < work.divisions.length; i++) {
      var d = work.divisions[i];
      html += '<li><button type="button" data-book="' + d.n + '">' +
        "<span>" + esc(work.noun) + " " + d.n + "</span>" +
        '<span class="div-count">' + d.units + " " + esc(work.unit) +
        (d.units === 1 ? "" : "s") + "</span>" +
        (d.title ? '<span class="div-title">' + esc(d.title) + "</span>" : "") +
        "</button></li>";
    }
    el.list.innerHTML = html;
  }

  function wire() {
    el.list.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-book]");
      if (b) selectBook(+b.dataset.book);
    });

    el.text.addEventListener("click", function (e) {
      var span = e.target.closest(".w");
      if (span) {
        e.stopPropagation();
        if (span === activeWord) hidePopup();
        else showPopup(span);
      }
    });

    document.addEventListener("click", function (e) {
      if (el.popup.hidden) return;
      if (!el.popup.contains(e.target)) hidePopup();
    });

    el.popup.querySelector(".popup-close").addEventListener("click", hidePopup);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") hidePopup();
    });

    window.addEventListener("resize", function () {
      if (!el.popup.hidden && activeWord) position(activeWord);
    });

    el.jump.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      var ref = parseRef(el.jump.value);
      if (!ref) return;
      if (current && ref.book === current.book) {
        goToLine(ref.book, ref.line);
        history.replaceState(null, "", hashFor(work.id, ref.book, ref.line));
      } else {
        selectBook(ref.book, ref.line);
      }
      el.jump.blur();
    });

    document.getElementById("menu-toggle").addEventListener("click", function () {
      var open = el.sidebar.classList.toggle("open");
      this.setAttribute("aria-expanded", String(open));
    });

    var theme = document.getElementById("theme");
    if (localStorage.getItem("latin-theme") === "dark") {
      document.body.classList.add("dark");
    }
    theme.addEventListener("click", function () {
      var dark = document.body.classList.toggle("dark");
      localStorage.setItem("latin-theme", dark ? "dark" : "light");
    });

    window.addEventListener("hashchange", function () {
      var ref = fromHash();
      if (work && ref.id === work.id && current && ref.book === current.book) {
        if (ref.line) goToLine(ref.book, ref.line);
      } else {
        selectWork(ref.id, ref.book, ref.line, false);
      }
    });
  }

  function start() {
    return getJSON("data/works.json").then(function (d) {
      works = d.works || [];
      if (!works.length) throw new Error("no works listed in data/works.json");

      buildWorkList();
      wire();

      // The text is readable before the dictionary arrives; glosses fill in after.
      getJSON("data/lexicon.json").then(function (d) { lexicon = d; })
        .catch(function () { lexicon = {}; });

      var ref = fromHash();
      return selectWork(ref.id, ref.book, ref.line);
    }).catch(function (e) {
      el.text.innerHTML = '<p class="error">Could not start: ' + esc(e.message) + "</p>";
    });
  }

  start();
})();

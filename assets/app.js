/* Caesar, Cicero and Tacitus — an annotated reader.
 *
 * Every token rendered here is a distinct record from the LASLA Opera Latina
 * corpus, addressed by its position in the text. Nothing is looked up by
 * spelling, so two identically spelled words keep their own separate
 * analyses. The morphology is rendered at build time (see tools/lasla.py) and
 * printed here verbatim; the only thing looked up by key is the definition.
 */
(function () {
  "use strict";

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
    src: document.getElementById("p-src"),
    logeion: document.getElementById("p-logeion")
  };

  var lexicon = null;
  var works = [];           // from data/works.json
  var work = null;          // the work currently selected
  var current = null;       // the book currently rendered
  var tokens = [];          // flat token list for the rendered book
  var activeWord = null;
  var bookCache = {};

  function workById(id) {
    for (var i = 0; i < works.length; i++) {
      if (works[i].id === id) return works[i];
    }
    return null;
  }

  /* Books are not always 1..N — the Annals is missing 7 to 10. */
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

  /* ---------------- glosses ---------------- */

  /* LASLA lemmatises proper nouns in lower case ("roma", "seruius"). The
     lexicon matches case-insensitively, but a capital reads better as the
     dictionary form, and the corpus tells us which words are names. */
  function displayLemma(lemma, isName) {
    if (!lemma) return "";
    return isName ? lemma.charAt(0).toUpperCase() + lemma.slice(1) : lemma;
  }

  function glossFor(lemma, isName) {
    var hit = lexicon && Object.prototype.hasOwnProperty.call(lexicon, lemma)
      ? lexicon[lemma] : null;
    if (hit) return { text: hit[0], src: hit[1] === 0 ? "Wiktionary" : "Lewis & Short" };
    if (isName) return { text: "proper name", src: null, weak: true };
    if (!lemma) return { text: "no dictionary form recorded", src: null, weak: true };
    return { text: "no definition available", src: null, weak: true };
  }

  /* ---------------- rendering ---------------- */

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function render(book) {
    current = book;
    tokens = [];

    var div = divisionOf(work, book.book) || {};
    var many = work.divisions.length > 1;
    var html = ['<h2 class="book-title"><small>' + esc(work.authorLatin) +
      (many ? " · " + esc(work.noun) + " " + book.book : "") + "</small>" +
      esc(work.latin) + (many ? " " + book.book : "") + "</h2>"];

    if (work.note) html.push('<div class="prose-note">' + esc(work.note) + "</div>");

    for (var i = 0; i < book.lines.length; i++) {
      var line = book.lines[i];
      var pieces = [];

      for (var j = 0; j < line.w.length; j++) {
        var w = line.w[j];
        var idx = tokens.length;
        tokens.push({
          form: w[0],
          lemma: book.lemmas[w[1]],
          parse: book.parses[w[2]] || "",
          name: !!w[3],
          line: line.n
        });
        pieces.push((pieces.length ? " " : "") +
          '<span class="w' + (book.lemmas[w[1]] ? "" : " unknown") +
          '" data-t="' + idx + '">' + esc(w[0]) + "</span>");
      }

      html.push(
        '<div class="line prose" id="' + sectionId(book.book, line.n) + '">' +
        '<span class="lnum">' + esc(line.n) + "</span>" +
        '<span class="line-text">' + pieces.join("") + "</span>" +
        "</div>"
      );
    }

    el.text.innerHTML = html.join("");
    hidePopup();
  }

  /* Section labels carry dots ("12.3"), so they are encoded rather than
     interpolated straight into an id. */
  function sectionId(book, n) {
    return "l" + book + "_" + String(n).replace(/\./g, "-");
  }

  /* ---------------- popup ---------------- */

  function showPopup(span) {
    var t = tokens[+span.dataset.t];
    if (!t) return;

    if (activeWord) activeWord.classList.remove("active");
    activeWord = span;
    span.classList.add("active");

    var g = glossFor(t.lemma, t.name);
    var many = work.divisions.length > 1;

    el.form.textContent = t.form;
    el.ref.textContent = work.ref + " " + (many ? current.book + "." : "") + t.line;
    el.gloss.textContent = g.text;
    el.gloss.className = "p-gloss" + (g.weak ? " none" : "");
    el.lemma.textContent = displayLemma(t.lemma, t.name) || "—";
    el.lemma.className = t.lemma ? "latin-val" : "";
    el.parse.textContent = t.parse || "not annotated";
    el.src.textContent = g.src ? g.src : "";

    if (t.lemma) {
      el.logeion.href = "https://logeion.uchicago.edu/" +
        encodeURIComponent(displayLemma(t.lemma, t.name));
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

  function selectWork(id, n, sec, push) {
    var next = workById(id) || works[0];
    if (work !== next) {
      work = next;
      el.workAuthor.textContent = work.authorLatin;
      el.workName.textContent = work.latin;
      document.title = work.latin + " — an annotated Latin reader";
      buildBookList();
      Array.prototype.forEach.call(el.works.querySelectorAll("button"), function (b) {
        var on = b.dataset.work === work.id;
        b.setAttribute("aria-current", String(on));
        b.setAttribute("aria-checked", String(on));
        if (on) b.scrollIntoView({ block: "nearest" });
      });
      el.booksHead.textContent = work.divisions.length > 1
        ? plural(work.noun) : "Sections";
      el.booksHead.hidden = work.divisions.length < 2;
      el.list.hidden = work.divisions.length < 2;
      // A one-book work is numbered straight through, so its section count is
      // also its last section — a more useful hint than "1".
      el.jump.placeholder = "e.g. " + (work.divisions.length > 1
        ? work.divisions[0].n + "." + work.divisions[0].first
        : work.divisions[0].units);
    }
    return selectBook(n || work.divisions[0].n, sec, push);
  }

  function selectBook(n, sec, push) {
    n = n | 0;
    if (!divisionOf(work, n)) n = work.divisions[0].n;
    el.text.innerHTML = '<p class="loading">Loading…</p>';

    Array.prototype.forEach.call(el.list.querySelectorAll("button"), function (b) {
      b.setAttribute("aria-current", String(+b.dataset.book === n));
    });

    return loadBook(work.id, n).then(function (book) {
      render(book);
      if (sec) {
        goToSection(n, sec);
      } else {
        el.reader.scrollTop = 0;
        window.scrollTo(0, 0);
      }
      if (push !== false) {
        history.replaceState(null, "", hashFor(work.id, n, sec));
      }
      el.sidebar.classList.remove("open");
    }).catch(function (e) {
      el.text.innerHTML = '<p class="error">Could not load ' + esc(work.latin) +
        " " + n + ". " + esc(e.message) + "</p>";
    });
  }

  function goToSection(book, sec) {
    var target = document.getElementById(sectionId(book, sec));
    if (!target) return false;
    Array.prototype.forEach.call(el.text.querySelectorAll(".line.target"),
      function (d) { d.classList.remove("target"); });
    target.classList.add("target");
    target.scrollIntoView({ block: "center", behavior: "smooth" });
    return true;
  }

  /* "1.90.20" -> book 1, section "90.20"; "1.5" -> book 1, section "5".
     A work with only one book takes the whole string as the section. */
  function parseRef(s) {
    var m = /^\s*(\d{1,3}(?:[.:]\d{1,4}){0,2})\s*$/.exec(s || "");
    if (!m) return null;
    var parts = m[1].split(/[.:]/);
    if (work && work.divisions.length < 2) {
      return { book: work.divisions[0].n, sec: parts.join(".") };
    }
    return { book: +parts[0], sec: parts.slice(1).join(".") };
  }

  function hashFor(id, book, sec) {
    return "#" + id + "." + book + (sec ? "." + sec : "");
  }

  /* "#tacitus-annales.1.5" — the leading component is always the work id. */
  function fromHash() {
    var raw = decodeURIComponent(location.hash.replace(/^#/, ""));
    var m = /^([A-Za-z][A-Za-z0-9_-]*)\.(.+)$/.exec(raw);
    if (m && workById(m[1])) {
      var parts = m[2].split(".");
      return { id: m[1], book: +parts[0], sec: parts.slice(1).join(".") };
    }
    return { id: works[0].id, book: 0, sec: "" };
  }

  /* ---------------- wiring ---------------- */

  function buildWorkList() {
    var html = "";
    var seen = null;
    for (var i = 0; i < works.length; i++) {
      var w = works[i];
      if (w.author !== seen) {
        seen = w.author;
        html += '<li class="author-head">' + esc(w.author) + "</li>";
      }
      html += '<li><button type="button" role="radio" aria-checked="false" data-work="' +
        esc(w.id) + '"><span class="latin">' + esc(w.latin) + "</span>" +
        '<span class="div-title">' + esc(w.title) + "</span></button></li>";
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
        (d.units === 1 ? "" : "s") + "</span></button></li>";
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
        goToSection(ref.book, ref.sec);
        history.replaceState(null, "", hashFor(work.id, ref.book, ref.sec));
      } else {
        selectBook(ref.book, ref.sec);
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
        if (ref.sec) goToSection(ref.book, ref.sec);
      } else {
        selectWork(ref.id, ref.book, ref.sec, false);
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
      return selectWork(ref.id, ref.book, ref.sec);
    }).catch(function (e) {
      el.text.innerHTML = '<p class="error">Could not start: ' + esc(e.message) + "</p>";
    });
  }

  start();
})();

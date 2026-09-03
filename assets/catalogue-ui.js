/* Search and filtering for the static catalogue pages.
 *
 * Three independent enhancements, each activating only if its markup is on the
 * page. Everything the page needs to render is already in the HTML; this only
 * adds filtering on top, so the pages stay useful with JS disabled or blocked.
 *
 *   1. global search   : products from a 4KB index loaded up front; part
 *                        numbers from a 42KB index fetched on first keystroke
 *   2. brand filter    : category pages, from data-brands on each card
 *   3. spec filter     : product pages, filters rows across all brand tables
 */
(function () {
  "use strict";

  var norm = function (s) {
    return String(s).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  };

  // Base64, not a literal, so the address isn't plaintext in this file.
  var SALES_EMAIL = atob("c2FsZXNAcmJhbGFqaWVudC5jb20=");

  // ---------------------------------------------------------------- search
  function initSearch() {
    var box = document.querySelector("[data-search]");
    if (!box) return;

    var input = box.querySelector("input");
    var panel = box.querySelector("[data-results]");
    var products = null;
    var parts = null;
    var partsPending = false;
    var active = -1;
    var rows = [];

    box.hidden = false;

    // Assets are cached for a day, so the pages hand us a content version to
    // append; a rebuilt index is a new URL rather than a stale cache hit.
    var v = box.dataset.indexV ? "?v=" + box.dataset.indexV : "";

    fetch("/assets/search-index.json" + v)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        products = d.map(function (p) {
          return { p: p, k: norm(p.n + " " + p.c + " " + p.s + " " + p.b.join(" ")) };
        });
        if (input.value) run();
      })
      .catch(function () { /* search stays inert; the page still works */ });

    function loadParts() {
      if (parts || partsPending) return;
      partsPending = true;
      fetch("/assets/parts-index.json" + v)
        .then(function (r) { return r.json(); })
        .then(function (d) {
          parts = d.map(function (x) { return { id: x[0], u: x[1], k: norm(x[0]) }; });
          run();
        })
        .catch(function () { partsPending = false; });
    }

    function esc(s) {
      return String(s).replace(/[&<>"]/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
      });
    }

    function run() {
      var qRaw = input.value.trim();
      var q = norm(qRaw);
      if (q.length < 2) { close(); return; }

      var terms = q.split(" ");
      var hits = [];

      if (products) {
        for (var i = 0; i < products.length && hits.length < 40; i++) {
          var ok = true;
          for (var t = 0; t < terms.length; t++) {
            if (products[i].k.indexOf(terms[t]) === -1) { ok = false; break; }
          }
          if (ok) hits.push(products[i].p);
        }
        // whole-word / prefix matches on the product name first
        hits.sort(function (a, b) {
          var an = norm(a.n), bn = norm(b.n);
          return (bn.indexOf(q) === 0) - (an.indexOf(q) === 0)
              || (bn.indexOf(q) > -1) - (an.indexOf(q) > -1)
              || an.length - bn.length;
        });
      }

      // A query with a digit is probably a part number.
      var partHits = [];
      if (/\d/.test(qRaw)) {
        loadParts();
        if (parts) {
          for (var j = 0; j < parts.length && partHits.length < 8; j++) {
            if (parts[j].k.indexOf(q) !== -1) partHits.push(parts[j]);
          }
        }
      }

      render(hits.slice(0, 8), partHits, qRaw);
    }

    function render(hits, partHits, q) {
      rows = [];
      var html = "";

      if (hits.length) {
        html += '<div class="sr-group">Products</div>';
        hits.forEach(function (p) {
          rows.push(p.u);
          html += '<a class="sr-row" href="' + p.u + '">'
                + '<span class="sr-name">' + esc(p.n) + "</span>"
                + '<span class="sr-meta">' + esc(p.c) + " &middot; " + esc(p.s) + "</span></a>";
        });
      }

      if (partHits.length) {
        html += '<div class="sr-group">Part numbers</div>';
        partHits.forEach(function (p) {
          rows.push(p.u);
          html += '<a class="sr-row" href="' + p.u + '">'
                + '<span class="sr-name">' + esc(p.id) + "</span>"
                + '<span class="sr-meta">View product</span></a>';
        });
      }

      if (!html) {
        if (partsPending && !parts) {
          html = '<div class="sr-empty">Searching part numbers&hellip;</div>';
        } else {
          html = '<div class="sr-empty">Nothing matches &ldquo;' + esc(q)
               + '&rdquo;. Try a shorter term, or <a href="mailto:' + SALES_EMAIL + '">ask us</a>.</div>';
        }
      }

      panel.innerHTML = html;
      panel.hidden = false;
      input.setAttribute("aria-expanded", "true");
      active = -1;
    }

    function close() {
      panel.hidden = true;
      panel.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
      active = -1;
    }

    function move(d) {
      var els = panel.querySelectorAll(".sr-row");
      if (!els.length) return;
      active = (active + d + els.length) % els.length;
      for (var i = 0; i < els.length; i++) els[i].classList.toggle("on", i === active);
      els[active].scrollIntoView({ block: "nearest" });
    }

    var timer;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(run, 90);
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown") { ev.preventDefault(); move(1); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); move(-1); }
      else if (ev.key === "Enter") {
        var els = panel.querySelectorAll(".sr-row");
        var pick = active > -1 ? els[active] : els[0];
        if (pick) { ev.preventDefault(); window.location.href = pick.getAttribute("href"); }
      } else if (ev.key === "Escape") { close(); input.blur(); }
    });
    document.addEventListener("click", function (ev) {
      if (!box.contains(ev.target)) close();
    });
  }

  // ---------------------------------------------------------- brand filter
  function initBrandFilter() {
    var bar = document.querySelector("[data-brand-filter]");
    if (!bar) return;

    var cards = [].slice.call(document.querySelectorAll(".type-card"));
    if (!cards.length) return;

    var counts = {};
    cards.forEach(function (c) {
      (c.dataset.brands || "").split("|").filter(Boolean).forEach(function (b) {
        counts[b] = (counts[b] || 0) + 1;
      });
    });
    var names = Object.keys(counts).sort(function (a, b) {
      return counts[b] - counts[a] || a.localeCompare(b);
    });
    if (names.length < 2) return;

    var chips = names.map(function (b) {
      return '<button type="button" class="chip" data-brand="' + b + '">'
           + b + '<span class="chip-n">' + counts[b] + "</span></button>";
    }).join("");
    bar.innerHTML = '<span class="filter-label">Brand</span>'
                  + '<div class="chip-row">' + chips + "</div>"
                  + '<button type="button" class="chip-clear" hidden>Clear</button>'
                  + '<span class="filter-count" role="status"></span>';
    bar.hidden = false;

    var on = {};
    var clear = bar.querySelector(".chip-clear");
    var count = bar.querySelector(".filter-count");

    function apply() {
      var sel = Object.keys(on).filter(function (k) { return on[k]; });
      var shown = 0;
      cards.forEach(function (c) {
        var bs = (c.dataset.brands || "").split("|");
        var vis = !sel.length || sel.some(function (s) { return bs.indexOf(s) > -1; });
        c.hidden = !vis;
        if (vis) shown++;
      });
      // hide a subcategory heading whose products are all filtered out
      [].forEach.call(document.querySelectorAll(".sub-block"), function (b) {
        var any = [].some.call(b.querySelectorAll(".type-card"), function (c) {
          return !c.hidden;
        });
        b.hidden = !any;
      });
      clear.hidden = !sel.length;
      count.textContent = sel.length
        ? "Showing " + shown + " of " + cards.length + " products"
        : "";
    }

    bar.addEventListener("click", function (ev) {
      var chip = ev.target.closest(".chip");
      if (chip) {
        var b = chip.dataset.brand;
        on[b] = !on[b];
        chip.classList.toggle("on", on[b]);
        chip.setAttribute("aria-pressed", on[b] ? "true" : "false");
        apply();
        return;
      }
      if (ev.target.closest(".chip-clear")) {
        on = {};
        [].forEach.call(bar.querySelectorAll(".chip"), function (c) {
          c.classList.remove("on");
          c.setAttribute("aria-pressed", "false");
        });
        apply();
      }
    });
  }

  // ----------------------------------------------------------- spec filter
  function initSpecFilter() {
    var wrap = document.querySelector("[data-spec-filter]");
    if (!wrap) return;

    var blocks = [].slice.call(document.querySelectorAll(".brand-block"));
    var all = [];
    blocks.forEach(function (b) {
      [].forEach.call(b.querySelectorAll("tbody tr"), function (tr) {
        all.push({ tr: tr, block: b, k: norm(tr.textContent) });
      });
    });
    if (all.length < 8) return;

    wrap.innerHTML = '<label class="sr-only" for="spec-q">Filter sizes and part numbers</label>'
      + '<input id="spec-q" type="search" placeholder="Filter ' + all.length
      + ' sizes, try a size or part number" autocomplete="off">'
      + '<span class="filter-count" role="status"></span>';
    wrap.hidden = false;

    var input = wrap.querySelector("input");
    var count = wrap.querySelector(".filter-count");

    function apply() {
      var q = norm(input.value);
      var terms = q ? q.split(" ") : [];
      var shown = 0;
      all.forEach(function (r) {
        var vis = true;
        for (var i = 0; i < terms.length; i++) {
          if (r.k.indexOf(terms[i]) === -1) { vis = false; break; }
        }
        r.tr.hidden = !vis;
        if (vis) shown++;
      });
      blocks.forEach(function (b) {
        var any = [].some.call(b.querySelectorAll("tbody tr"), function (tr) {
          return !tr.hidden;
        });
        b.hidden = !any;
      });
      count.textContent = terms.length
        ? shown + " of " + all.length + " sizes"
        : "";
    }

    var timer;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(apply, 80);
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") { input.value = ""; apply(); }
    });
  }

  function boot() {
    initSearch();
    initBrandFilter();
    initSpecFilter();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

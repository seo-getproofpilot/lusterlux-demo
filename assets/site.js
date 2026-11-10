/* LusterLux — shared behaviour. No framework, no build step.
   Scrolling is native on purpose: a hijacked wheel adds input latency you cannot
   tune away. Anchor jumps stay smooth via scroll-behavior + scroll-margin-top. */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };

  /* ---------- review switches ----------
     ?type=a|b|c and ?btn=a|b|c let the type and button directions be compared
     on the real page instead of from a description. Default (no param) is
     direction A, so nothing changes for a normal visitor. Alternate display
     families are only fetched when actually asked for. */
  (function () {
    var q = new URLSearchParams(location.search);
    var ty = (q.get('type') || '').toLowerCase(), bt = (q.get('btn') || '').toLowerCase();
    if (/^[abc]$/.test(ty)) {
      document.documentElement.setAttribute('data-type', ty);
      var fam = ty === 'b' ? 'Bodoni+Moda:ital,opsz,wght@0,6..96,400..800;1,6..96,400..700'
              : ty === 'c' ? 'Sora:wght@300;400;600;700' : null;
      if (fam) {
        var l = document.createElement('link');
        l.rel = 'stylesheet';
        l.href = 'https://fonts.googleapis.com/css2?family=' + fam + '&display=swap';
        document.head.appendChild(l);
      }
    }
    if (/^[abc]$/.test(bt)) document.documentElement.setAttribute('data-btn', bt);
  })();

  /* ---------- nav ---------- */
  var nav = $('#nav'), burger = $('#burger'), panel = $('#mpanel');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 24); };
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }
  if (burger && panel) {
    burger.addEventListener('click', function () {
      var open = panel.classList.toggle('open');
      burger.setAttribute('aria-expanded', String(open));
      document.documentElement.style.overflow = open ? 'hidden' : '';
    });
    $$('a', panel).forEach(function (a) {
      a.addEventListener('click', function () {
        panel.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
        document.documentElement.style.overflow = '';
      });
    });
  }

  /* ---------- reveals ---------- */
  var SEL = '.fade,.slide,.mask,.dive-r,.dive-l';
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -6% 0px' });
    $$(SEL).forEach(function (e) { io.observe(e); });
  } else {
    $$(SEL).forEach(function (e) { e.classList.add('in'); });
  }
  var queued = false;
  function sweepNow() {
    queued = false;
    var left = $$(SEL + ':not(.in)');
    if (!left.length) { window.removeEventListener('scroll', sweep); window.removeEventListener('resize', sweep); return; }
    var vh = window.innerHeight;
    left.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.95 && r.bottom > -60) el.classList.add('in');
    });
  }
  function sweep() { if (!queued) { queued = true; requestAnimationFrame(sweepNow); } }
  window.addEventListener('scroll', sweep, { passive: true });
  window.addEventListener('resize', sweep, { passive: true });
  window.addEventListener('load', sweep);
  sweep();
  window.LLreveal = function () { $$(SEL).forEach(function (e) { e.classList.add('in'); }); };

  /* ---------- hero plates ---------- */
  var heroBg = $('#heroBg');
  if (heroBg) {
    $$('.rev').forEach(function (e) { setTimeout(function () { e.classList.add('in'); }, 90); });
    var plates = $$('figure', heroBg), dots = $$('#heroDots button'), i = 0, timer;
    var fadeT;
    function go(n) {
      var from = i;
      i = (n + plates.length) % plates.length;
      if (i === from) return;
      plates.forEach(function (p, k) {
        p.classList.toggle('on', k === i);
        p.classList.toggle('prev', k === from);
      });
      dots.forEach(function (d, k) { d.setAttribute('aria-current', String(k === i)); });
      clearTimeout(fadeT);
      fadeT = setTimeout(function () {
        plates.forEach(function (p) { p.classList.remove('prev'); });
      }, 1600);
    }
    dots.forEach(function (d, k) { d.addEventListener('click', function () { go(k); restart(); }); });
    function restart() {
      clearInterval(timer);
      if (!reduced && plates.length > 1) timer = setInterval(function () { go(i + 1); }, 6800);
    }
    plates.forEach(function (p, k) { p.classList.toggle('on', k === 0); });
    restart();
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) clearInterval(timer); else restart();
    });
  }

  /* ---------- hero parallax (one element, transform only) ---------- */
  if (!reduced) {
    var pars = $$('[data-par]'), ticking = false;
    if (pars.length) {
      var run = function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
          var vh = window.innerHeight;
          pars.forEach(function (el) {
            var r = el.getBoundingClientRect();
            if (r.bottom < -160 || r.top > vh + 160) return;
            var p = (r.top + r.height / 2 - vh / 2) / vh;
            el.style.transform = 'translate3d(0,' + (p * parseFloat(el.dataset.par)).toFixed(1) + 'px,0)';
          });
          ticking = false;
        });
      };
      window.addEventListener('scroll', run, { passive: true });
      window.addEventListener('resize', run, { passive: true });
      run();
    }
  }

  /* ---------- Instagram reels ----------
     Hover (or keyboard focus) plays the clip muted. Sound NEVER starts from a
     hover — a site may not begin playing audio on its own, and browsers block
     audible autoplay anyway. The unmute button is the only route to sound and
     needs a real click; unmuting one reel mutes the others so two clips can
     never talk over each other. */
  var reels = $$('.ig-reel.has-vid');
  if (reels.length) {
    var loud = null;
    reels.forEach(function (r) {
      var v = $('video', r), btn = $('[data-sound]', r);
      if (!v) return;
      var play = function () {
        var pr = v.play();
        if (pr && pr.catch) pr.catch(function () { /* blocked: poster stays */ });
      };
      var stop = function () {
        v.pause();
        if (loud !== v) { try { v.currentTime = 0; } catch (e) {} }
      };
      r.addEventListener('mouseenter', play);
      r.addEventListener('mouseleave', stop);
      r.addEventListener('focusin', play);
      r.addEventListener('focusout', stop);
      if (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault(); e.stopPropagation();
          var makeLoud = v.muted;
          reels.forEach(function (o) {
            var ov = $('video', o), ob = $('[data-sound]', o);
            if (!ov) return;
            ov.muted = true;
            if (ob) { ob.setAttribute('aria-pressed', 'false');
                      ob.setAttribute('aria-label', 'Unmute this reel'); }
            o.classList.remove('loud');
          });
          if (makeLoud) {
            v.muted = false; loud = v;
            btn.setAttribute('aria-pressed', 'true');
            btn.setAttribute('aria-label', 'Mute this reel');
            r.classList.add('loud');
            play();
          } else { loud = null; }
        });
      }
    });
  }

  /* ---------- guides rail ---------- */
  var gRail = $('#gRail');
  if (gRail) {
    var gStep = function () { return Math.min(gRail.clientWidth * 0.8, 420); };
    var gp = $('#gPrev'), gn = $('#gNext');
    if (gp) gp.addEventListener('click', function () { gRail.scrollBy({ left: -gStep(), behavior: 'smooth' }); });
    if (gn) gn.addEventListener('click', function () { gRail.scrollBy({ left: gStep(), behavior: 'smooth' }); });
  }

  /* ---------- reviews conveyor ----------
     The clone run is offset by the first run's exact width so the loop has no
     visible seam at any card count, and the duration scales with that width to
     keep a constant speed. */
  var belt = $('#revBelt');
  if (belt) {
    var runs = $$('.belt-run', belt);
    var sizeBelt = function () {
      var w = runs[0].scrollWidth;
      if (!w) return;
      if (runs[1]) runs[1].style.left = w + 'px';
      var dur = Math.max(28, Math.round(w / 42));
      runs.forEach(function (r) { r.style.animationDuration = dur + 's'; });
    };
    sizeBelt();
    window.addEventListener('resize', sizeBelt, { passive: true });
    window.addEventListener('load', sizeBelt);
  }

  /* ---------- The Line: pinned deck ----------
     The three states are metriccivil.ca's own, read out of its Webflow IX2
     action list rather than eyeballed:

       upcoming  translate(107%, 85%)  scale(.20, .15)   thumbnail, bottom right
       active    translate(0, 0)       scale(1, 1)       fills the frame
       past      translate(-26%, 0)    scale(.20, .15)   thumbnail, parked left

     So the next photo blooms out of the bottom-right corner while the current
     one shrinks away to the left. transform-origin is 0 0 — those percentages
     are measured from the element's own top-left.

     One rAF-throttled handler, transform/opacity only, no filters on anything
     that moves. */
  var scope = document.getElementById('line');
  var track = document.getElementById('scopeTrack');
  var reducedM = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (scope && track) {
    var sCards = $$('.scope-card', track);
    var bar = document.getElementById('scopeBar');
    scope.style.setProperty('--n', sCards.length);
    var figs = sCards.map(function (c) { return $('.scope-fig', c); });
    var cops = sCards.map(function (c) { return $('.scope-copy', c); });
    var pinned = false, ticking = false;

    var UP   = { x: 107, y: 85, sx: 0.20, sy: 0.15 };
    var ON   = { x: 0,   y: 0,  sx: 1,    sy: 1    };
    var PAST = { x: -26, y: 0,  sx: 0.20, sy: 0.15 };
    function lerp(a, b, t) { return a + (b - a) * t; }
    function ease(t) { return t * t * (3 - 2 * t); }          // smoothstep
    function mix(a, b, t) {
      return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t),
               sx: lerp(a.sx, b.sx, t), sy: lerp(a.sy, b.sy, t) };
    }

    function layout() {
      pinned = window.innerWidth >= 1000 && !reducedM.matches;
      if (!pinned) {
        sCards.forEach(function (c, i) {
          c.style.visibility = ''; c.style.zIndex = '';
          figs[i].style.transform = ''; cops[i].style.transform = ''; cops[i].style.opacity = '';
        });
      }
      render();
    }

    function render() {
      if (!pinned) return;
      var r = scope.getBoundingClientRect();
      var span = scope.offsetHeight - window.innerHeight;
      var p = span > 0 ? Math.min(1, Math.max(0, -r.top / span)) : 0;
      var pos = p * (sCards.length - 1);
      for (var i = 0; i < sCards.length; i++) {
        var d = i - pos;                       // <0 already passed, >0 still coming
        var vis = d > -1.15 && d < 1.15;
        sCards[i].style.visibility = vis ? 'visible' : 'hidden';
        if (!vis) continue;
        sCards[i].style.zIndex = String(20 - Math.round(Math.abs(d) * 10));
        var st = d <= -1 ? PAST
               : d >= 1  ? UP
               : d <= 0  ? mix(ON, PAST, ease(-d))     // active -> parked left
                         : mix(UP, ON, ease(1 - d));   // corner thumb -> active
        figs[i].style.transform =
          'translate(' + st.x.toFixed(2) + '%,' + st.y.toFixed(2) + '%) ' +
          'scale(' + st.sx.toFixed(4) + ',' + st.sy.toFixed(4) + ')';
        // Copy stays in its column and only cross-fades, sharply — every card's
        // copy shares one column, so two legible blocks would overlap into mush.
        var ad = Math.abs(d);
        cops[i].style.transform = 'translate3d(0,' + (d * 34).toFixed(1) + 'px,0)';
        cops[i].style.opacity = String(Math.min(1, Math.max(0, (0.5 - ad) / 0.16)));
      }
      if (bar) bar.style.width = (p * 100).toFixed(1) + '%';
    }

    // Driven by a rAF loop that runs only while the section is on screen, not by
    // scroll events. A scroll listener assumes every scroll reaches this window
    // — smooth-scroll shims, embedded contexts and trackpad momentum can all
    // break that, and the failure is silent: the section just scrolls past with
    // nothing happening. The loop costs one frame's work while in view and
    // stops the moment the section leaves.
    var running = false;
    function tick() { if (!running) return; render(); requestAnimationFrame(tick); }
    function start() { if (!running) { running = true; requestAnimationFrame(tick); } }
    function stop() { running = false; }

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es[0].isIntersecting ? start() : (stop(), render());
      }, { rootMargin: '25% 0px' }).observe(scope);
    } else {
      start();
    }
    // Belt and braces: a plain scroll listener still nudges a render, so the
    // first paint is right even before the observer has reported in.
    function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; render(); }); } }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { layout(); }, { passive: true });
    if (reducedM.addEventListener) reducedM.addEventListener('change', layout);
    layout();
  }

  /* ---------- kit builder ----------
     ITM's count configurator, translated: there is nothing to book here, so
     the end of the flow is simply a filled cart. It only ever assembles
     handles that exist in the catalog, every price is the live store price,
     and the saving against a system kit is computed, never claimed. */
  var kitOut = document.getElementById('kitOut');
  if (kitOut && window.LL_KIT && window.LL && window.LL.products) {
    var K = window.LL_KIT, P = window.LL.products;
    var byH = {};
    P.forEach(function (p) { byH[p.h] = p; });
    var surf = 'car-truck', jobs = [];

    var money = function (n) { return '$' + n.toFixed(2); };

    function chosen() {
      var seen = {}, list = [];
      var m = (K.map || {})[surf] || {};
      jobs.forEach(function (jk) {
        var r = m[jk]; if (!r) return;
        [r.p, r.x].forEach(function (h) {
          var pr = byH[h];
          if (pr && !pr.soon && !seen[h]) { seen[h] = 1; list.push(pr); }
        });
      });
      return list;
    }

    /* The system kit that covers every job picked, offered with its REAL
       numbers. Their kits usually cost more than the two parts the finder
       names, because they bundle more in — so this says "steps up to" and
       lists what it adds, and only claims a saving when there is one. */
    function kitOffer(sum) {
      var m = (K.map || {})[surf] || {}, ks = {};
      jobs.forEach(function (jk) { if (m[jk]) { ks[m[jk].k] = (ks[m[jk].k] || 0) + 1; } });
      var names = Object.keys(ks);
      if (names.length !== 1 || ks[names[0]] !== jobs.length) return null;
      var kp = byH[names[0]];
      if (!kp || kp.soon) return null;
      return { p: kp, save: sum - kp.price };
    }

    function render() {
      if (!jobs.length) {
        kitOut.innerHTML = '<p class="kit-empty">Pick at least one job and the kit builds itself.</p>';
        return;
      }
      var list = chosen();
      if (!list.length) {
        kitOut.innerHTML = '<p class="kit-empty">Nothing in the line covers that combination yet.</p>';
        return;
      }
      var sum = 0;
      list.forEach(function (p) { sum += p.price; });

      var rows = list.map(function (p) {
        return '<li class="kit-row">'
          + '<a class="kit-fig" href="' + p.url + '" tabindex="-1" aria-hidden="true">'
          + '<img src="' + (window.LL_BASE || '') + '/assets/products/' + p.img + '-sm.webp" alt="" loading="lazy" decoding="async" /></a>'
          + '<div class="kit-nm"><a href="' + p.url + '">' + p.n + '</a><span>' + p.fn + '</span></div>'
          + '<span class="kit-pr">' + money(p.price) + '</span></li>';
      }).join('');

      var off = kitOffer(sum);
      var alt = '';
      if (off) {
        var inc = (off.p.includes || []).slice(0, 3).join(' &middot; ');
        var line = off.save > 0
          ? '<em>save ' + money(off.save) + '</em>'
          : '<em>' + money(off.p.price - sum) + ' more</em>';
        alt = '<div class="kit-alt"><p class="kit-alt-h">Or step up</p>'
            + '<p><b>' + off.p.n + '</b> covers all of this for ' + money(off.p.price)
            + ' &mdash; ' + line + '</p>'
            + (inc ? '<p class="kit-alt-inc">' + inc + '</p>' : '')
            + '<button class="btn btn-ghost btn-sm" type="button" id="kitAlt" data-h="'
            + off.p.h + '">Use the system instead</button></div>';
      }

      kitOut.innerHTML =
        '<div class="kit-list-head"><p>Your kit</p><span>' + list.length + ' product'
        + (list.length === 1 ? '' : 's') + '</span></div>'
        + '<ul class="kit-list">' + rows + '</ul>' + alt
        + '<div class="kit-total"><span>Total</span><b>' + money(sum) + '</b></div>'
        + '<button class="btn btn-primary kit-add" type="button" id="kitAdd">Add ' + list.length
        + ' to cart<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button>';

      document.getElementById('kitAdd').addEventListener('click', function () {
        if (!window.LLCart) return;
        // add() opens the drawer itself, so adding N products must not also
        // call open N times — the last add leaves it open on the full cart.
        list.forEach(function (p) { window.LLCart.add(p.h, 1); });
      });
      var ab = document.getElementById('kitAlt');
      if (ab) {
        ab.addEventListener('click', function () {
          if (!window.LLCart) return;
          window.LLCart.add(ab.getAttribute('data-h'), 1);
        });
      }
    }

    function mark() {
      $$('#kitSurf .kkey').forEach(function (b) {
        var on = b.getAttribute('data-k') === surf;
        b.classList.toggle('on', on);
        b.setAttribute('aria-pressed', String(on));
      });
      $$('#kitJob .kkey').forEach(function (b) {
        var on = jobs.indexOf(b.getAttribute('data-k')) > -1;
        b.classList.toggle('on', on);
        b.setAttribute('aria-pressed', String(on));
      });
    }

    $$('#kitSurf .kkey').forEach(function (b) {
      b.addEventListener('click', function () {
        surf = b.getAttribute('data-k'); mark(); render();
      });
    });
    $$('#kitJob .kkey').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.getAttribute('data-k'), i = jobs.indexOf(k);
        if (i > -1) { jobs.splice(i, 1); } else { jobs.push(k); }
        mark(); render();
      });
    });
    mark(); render();
  }

  /* ---------- collection: search + sort over the server-rendered grid ---------- */
  var grid = $('#grid'), q = $('#q'), sortEl = $('#sort'), countEl = $('#count');
  if (grid && q && sortEl) {
    var cards = $$('.card', grid);
    var meta = cards.map(function (c, idx) {
      var price = parseFloat((($('.card-price', c) || {}).textContent || '0').replace(/[^0-9.]/g, '')) || 0;
      return { el: c, idx: idx, price: price,
               name: (($('h3 a', c) || {}).textContent || '').trim(),
               text: c.textContent.toLowerCase() };
    });
    // Vehicle pages filter by product type in place: the URL keeps ?g= so the
    // choice survives a reload and a shared link, without a route per pair.
    var gbar = document.getElementById('gbar');
    var group = new URLSearchParams(location.search).get('g') || '';
    var apply = function () {
      var t = q.value.trim().toLowerCase();
      var shown = meta.filter(function (m) {
        var hit = (!t || m.text.indexOf(t) > -1) &&
                  (!group || m.el.getAttribute('data-group') === group);
        m.el.hidden = !hit;
        return hit;
      });
      var s = sortEl.value, order = shown.slice();
      if (s === 'price-asc')  order.sort(function (a, b) { return a.price - b.price; });
      if (s === 'price-desc') order.sort(function (a, b) { return b.price - a.price; });
      if (s === 'name')       order.sort(function (a, b) { return a.name.localeCompare(b.name); });
      if (s === 'featured')   order.sort(function (a, b) { return a.idx - b.idx; });
      order.forEach(function (m) { grid.appendChild(m.el); });
      if (countEl) countEl.textContent = shown.length + (shown.length === 1 ? ' product' : ' products');
      var empty = $('.empty', grid);
      if (!shown.length && !empty) {
        var p = document.createElement('p');
        p.className = 'empty'; p.textContent = 'Nothing matches that.';
        grid.appendChild(p);
      } else if (shown.length && empty) { empty.remove(); }
    };
    var t0; q.addEventListener('input', function () { clearTimeout(t0); t0 = setTimeout(apply, 130); });
    sortEl.addEventListener('change', apply);
    if (gbar) {
      var chips = $$('.gchip', gbar);
      var mark = function () {
        chips.forEach(function (c) { c.classList.toggle('on', (c.getAttribute('data-g') || '') === group); });
      };
      chips.forEach(function (c) {
        c.addEventListener('click', function () {
          group = c.getAttribute('data-g') || '';
          mark(); apply();
          var u = new URL(location.href);
          if (group) { u.searchParams.set('g', group); } else { u.searchParams.delete('g'); }
          history.replaceState(null, '', u);
        });
      });
      mark();
    }
    if (group) apply();
  }

  /* ---------- before / after drag compare ---------- */
  var baStage = $('#baStage');
  if (baStage) {
    var clip = $('#baClip'), range = $('#baRange'), handle = $('#baHandle');
    var inner = clip.querySelector('.ba-img');
    function sizeBA() {
      // the clipped image must stay the full stage width or the halves misalign
      inner.style.setProperty('--ba-w', baStage.clientWidth + 'px');
    }
    function setBA(pct) {
      pct = Math.max(0, Math.min(100, pct));
      clip.style.width = pct + '%';
      handle.style.left = pct + '%';
    }
    range.addEventListener('input', function () { setBA(parseFloat(range.value)); });
    window.addEventListener('resize', sizeBA, { passive: true });
    if (document.readyState === 'complete') sizeBA();
    else window.addEventListener('load', sizeBA);
    sizeBA(); setBA(parseFloat(range.value));
    /* nudge it once when it first scrolls into view, so it reads as draggable */
    if ('IntersectionObserver' in window && !reduced) {
      var teased = false;
      var bio = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (!e.isIntersecting || teased) return;
          teased = true; bio.disconnect();
          var t0 = null;
          requestAnimationFrame(function step(ts) {
            if (!t0) t0 = ts;
            var p = Math.min(1, (ts - t0) / 900);
            var v = 50 + Math.sin(p * Math.PI) * 16;
            setBA(v); range.value = v;
            if (p < 1) requestAnimationFrame(step); else { setBA(50); range.value = 50; }
          });
        });
      }, { threshold: 0.5 });
      bio.observe(baStage);
    }
  }

  /* ---------- find your product ---------- */
  var finder = $('#finder');
  if (finder && window.LL) {
    var out = $('#fqOut', finder);
    var steps = $$('.fq', finder);
    var pick = { s: null, j: null };
    var SLABEL = {}, JLABEL = {};
    $$('[data-s]', finder).forEach(function (b) { SLABEL[b.dataset.s] = b.textContent.trim(); });
    $$('[data-j]', finder).forEach(function (b) { JLABEL[b.dataset.j] = b.textContent.trim(); });

    function show(n) {
      steps.forEach(function (s, k) { s.hidden = (k !== n); });
      out.hidden = true;
    }
    function money(v) { return '$' + v.toFixed(2); }
    function byH(h) { return window.LL.products.filter(function (p) { return p.h === h; })[0]; }

    function result() {
      var url = (window.LL_BASE || '') + '/pages/find-your-product/' + pick.s + '-' + pick.j + '/';
      out.innerHTML = '<p class="fq-loading">Loading…</p>';
      out.hidden = false;
      steps.forEach(function (s) { s.hidden = true; });
      fetch(url).then(function (r) { return r.text(); }).then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var block = doc.querySelector('.res-out');
        out.innerHTML = '';
        if (block) out.appendChild(document.importNode(block, true));
        var again = document.createElement('button');
        again.type = 'button'; again.className = 'fq-back';
        again.textContent = '← Start over';
        again.addEventListener('click', function () { pick = { s: null, j: null }; clearOn(); show(0); });
        var perma = document.createElement('a');
        perma.className = 'tlink'; perma.href = url;
        perma.style.marginLeft = '22px';
        perma.textContent = 'Open this answer';
        var bar = document.createElement('p');
        bar.style.cssText = 'margin-top:26px;display:flex;flex-wrap:wrap;align-items:center;gap:10px 22px';
        bar.appendChild(again); bar.appendChild(perma);
        out.appendChild(bar);
      }).catch(function () { location.href = url; });
    }
    function clearOn() { $$('.fq-opt', finder).forEach(function (b) { b.classList.remove('on'); }); }

    finder.addEventListener('click', function (e) {
      var s = e.target.closest('[data-s]');
      if (s) { pick.s = s.dataset.s; clearOn(); s.classList.add('on'); show(1); return; }
      var j = e.target.closest('[data-j]');
      if (j) { pick.j = j.dataset.j; j.classList.add('on'); result(); return; }
      if (e.target.closest('[data-back]')) { show(0); }
    });
    show(0);
  }
})();

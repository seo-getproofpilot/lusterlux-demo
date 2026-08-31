/* LusterLux — shared behaviour. No framework, no build step.
   Scrolling is native on purpose: a hijacked wheel adds input latency you cannot
   tune away. Anchor jumps stay smooth via scroll-behavior + scroll-margin-top. */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };

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

    function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; render(); }); } }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { layout(); }, { passive: true });
    if (reducedM.addEventListener) reducedM.addEventListener('change', layout);
    layout();
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

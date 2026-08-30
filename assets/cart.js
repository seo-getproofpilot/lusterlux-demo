/* LusterLux — cart.
   State lives in localStorage. Checkout hands the basket to LusterLux's live
   Shopify checkout via a cart permalink built from real variant ids, so an order
   placed here is a real order. Nothing on this site ever touches payment details. */
(function () {
  'use strict';
  var KEY = 'll_cart_v1';
  var STORE = 'https://lusterluxauto.com';
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };

  var BASE = (window.LL_BASE || '');
  function catalog() { return (window.LL && window.LL.products) || []; }
  function find(h) { return catalog().filter(function (p) { return p.h === h; })[0]; }
  function freeAt() { return (window.LL && window.LL.meta && window.LL.meta.freeShipping) || 45; }

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; }
    catch (e) { return []; }
  }
  function write(items) {
    try { localStorage.setItem(KEY, JSON.stringify(items)); } catch (e) {}
    render();
    window.dispatchEvent(new CustomEvent('ll:cart', { detail: items }));
  }

  var Cart = {
    items: function () {
      // drop anything whose product has since left the catalog
      return read().filter(function (l) { return !!find(l.h); });
    },
    count: function () {
      return Cart.items().reduce(function (n, l) { return n + l.q; }, 0);
    },
    subtotal: function () {
      return Cart.items().reduce(function (n, l) {
        var p = find(l.h); return n + (p ? p.price * l.q : 0);
      }, 0);
    },
    add: function (h, q) {
      var p = find(h);
      if (!p || p.soon) return false;
      q = q || 1;
      var items = read(), hit = items.filter(function (l) { return l.h === h; })[0];
      if (hit) hit.q = Math.min(99, hit.q + q); else items.push({ h: h, q: q });
      write(items);
      open(h);
      return true;
    },
    setQty: function (h, q) {
      var items = read().map(function (l) { return l.h === h ? { h: h, q: Math.max(0, Math.min(99, q)) } : l; })
                        .filter(function (l) { return l.q > 0; });
      write(items);
    },
    remove: function (h) { write(read().filter(function (l) { return l.h !== h; })); },
    clear: function () { write([]); },
    checkoutUrl: function () {
      var parts = Cart.items().map(function (l) {
        var p = find(l.h); return p.vid + ':' + l.q;
      });
      return parts.length ? STORE + '/cart/' + parts.join(',') : STORE + '/cart';
    }
  };
  window.LLCart = Cart;

  /* ---------- drawer ---------- */
  function money(n) { return '$' + n.toFixed(2); }

  function render() {
    var items = Cart.items(), n = Cart.count(), sub = Cart.subtotal();
    $$('[data-cart-count]').forEach(function (el) {
      el.textContent = n;
      el.hidden = n === 0;
    });
    var list = $('#cartLines');
    if (!list) return;
    if (!items.length) {
      list.innerHTML = '<li class="cart-empty"><p>Your cart is empty.</p>' +
        '<a class="btn btn-line btn-sm" href="' + BASE + '/collections/">Shop the line</a></li>';
    } else {
      list.innerHTML = items.map(function (l) {
        var p = find(l.h);
        return '<li class="cart-line" style="--acc:' + p.acc + '">' +
          '<a class="cart-thumb" href="' + BASE + p.url + '"><img src="' + BASE + '/assets/products/' + p.img +
            '-sm.webp" alt="" loading="lazy" decoding="async" /></a>' +
          '<div class="cart-meta">' +
            '<a class="cart-name" href="' + BASE + p.url + '">' + p.n + '</a>' +
            '<span class="cart-fn">' + p.fn + (p.size ? ' &middot; ' + p.size : '') + '</span>' +
            '<div class="qty" role="group" aria-label="Quantity for ' + p.n + '">' +
              '<button type="button" data-qty="' + p.h + '" data-step="-1" aria-label="Decrease quantity">&minus;</button>' +
              '<span aria-live="polite">' + l.q + '</span>' +
              '<button type="button" data-qty="' + p.h + '" data-step="1" aria-label="Increase quantity">+</button>' +
            '</div>' +
          '</div>' +
          '<div class="cart-right">' +
            '<span class="cart-price">' + money(p.price * l.q) + '</span>' +
            '<button type="button" class="cart-rm" data-rm="' + p.h + '">Remove</button>' +
          '</div>' +
        '</li>';
      }).join('');
    }
    var subEl = $('#cartSub'); if (subEl) subEl.textContent = money(sub);
    var free = freeAt(), left = Math.max(0, free - sub);
    var bar = $('#cartFree');
    if (bar) {
      bar.innerHTML = left > 0
        ? '<span>' + money(left) + ' away from free shipping</span>' +
          '<i style="width:' + Math.min(100, (sub / free) * 100).toFixed(1) + '%"></i>'
        : '<span class="ok">Free shipping unlocked</span><i style="width:100%"></i>';
    }
    var co = $('#cartCheckout');
    if (co) { co.href = Cart.checkoutUrl(); co.setAttribute('aria-disabled', String(!items.length)); }
  }

  var lastFocus = null;
  function open(highlight) {
    var d = $('#cartDrawer'); if (!d) return;
    lastFocus = document.activeElement;
    d.classList.add('open');
    d.setAttribute('aria-hidden', 'false');
    document.documentElement.style.overflow = 'hidden';
    var close = $('#cartClose'); if (close) close.focus();
    if (highlight) {
      var line = $('.cart-line', d);
      if (line) { line.classList.add('flash'); setTimeout(function () { line.classList.remove('flash'); }, 700); }
    }
  }
  function close() {
    var d = $('#cartDrawer'); if (!d) return;
    d.classList.remove('open');
    d.setAttribute('aria-hidden', 'true');
    document.documentElement.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  window.LLCartOpen = open;

  document.addEventListener('click', function (e) {
    var add = e.target.closest('[data-add]');
    if (add) {
      e.preventDefault();
      if (Cart.add(add.getAttribute('data-add'), parseInt(add.getAttribute('data-qty') || '1', 10))) {
        // icon-only buttons carry an <svg>; rewriting textContent would destroy it
        var icon = !!add.querySelector('svg') && !add.classList.contains('btn');
        var was = icon ? null : add.textContent;
        add.classList.add('added');
        if (!icon) add.textContent = 'Added';
        setTimeout(function () {
          add.classList.remove('added');
          if (!icon) add.textContent = was;
        }, 1400);
      }
      return;
    }
    if (e.target.closest('[data-cart-open]')) { e.preventDefault(); open(); return; }
    if (e.target.closest('#cartClose') || e.target.closest('#cartScrim')) { close(); return; }
    var q = e.target.closest('[data-qty]');
    if (q) {
      var h = q.getAttribute('data-qty'), step = parseInt(q.getAttribute('data-step'), 10);
      var cur = (Cart.items().filter(function (l) { return l.h === h; })[0] || { q: 0 }).q;
      Cart.setQty(h, cur + step);
      return;
    }
    var rm = e.target.closest('[data-rm]');
    if (rm) { Cart.remove(rm.getAttribute('data-rm')); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });

  if (document.readyState !== 'loading') render();
  else document.addEventListener('DOMContentLoaded', render);
  /* another tab changed the cart */
  window.addEventListener('storage', function (e) { if (e.key === KEY) render(); });
})();

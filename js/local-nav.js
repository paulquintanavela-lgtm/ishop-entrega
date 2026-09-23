(function () {
  var SHOP_HOSTS = {
    "ec.tiendasishop.com": true,
    "www.tiendasishop.com": true,
    "tiendasishop.com": true,
    "co.tiendasishop.com": true,
    "cr.tiendasishop.com": true,
    "sv.tiendasishop.com": true,
    "pa.tiendasishop.com": true,
    "pe.tiendasishop.com": true,
    "tips.tiendasishop.com": true,
    "ishop-ecuador.myshopify.com": true,
  };

  function isAssetPath(pathname) {
    return (
      pathname.indexOf("/cdn/") === 0 ||
      pathname.indexOf("/web-pixels") === 0 ||
      pathname.indexOf("/wpm/") === 0
    );
  }

  function toLocalUrl(href, base) {
    if (!href || href.charAt(0) === "#" || href.indexOf("mailto:") === 0 || href.indexOf("tel:") === 0) {
      return null;
    }
    try {
      var url = new URL(href, base || window.location.origin);
      if (!SHOP_HOSTS[url.hostname]) return null;
      if (isAssetPath(url.pathname)) return null;
      if (url.pathname.indexOf("/customer_authentication") === 0) return "/account/";
      return url.pathname + url.search + url.hash;
    } catch (err) {
      return null;
    }
  }

  function rewriteAnchor(anchor) {
    if (!anchor || !anchor.getAttribute) return;
    var href = anchor.getAttribute("href");
    var local = toLocalUrl(href);
    if (!local) return;
    anchor.setAttribute("href", local);
    anchor.removeAttribute("target");
  }

  function rewriteAll(root) {
    var scope = root || document;
    if (!scope.querySelectorAll) return;
    var links = scope.querySelectorAll("a[href]");
    for (var i = 0; i < links.length; i += 1) rewriteAnchor(links[i]);
  }

  function keepClickLocal(event) {
    var link = event.target && event.target.closest ? event.target.closest("a[href]") : null;
    if (!link) return;
    var local = toLocalUrl(link.getAttribute("href")) || toLocalUrl(link.href);
    if (!local) return;
    event.preventDefault();
    event.stopPropagation();
    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
    window.location.assign(local);
  }

  document.addEventListener("click", keepClickLocal, true);
  document.addEventListener("auxclick", keepClickLocal, true);
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || !form.action) return;
    var local = toLocalUrl(form.getAttribute("action") || form.action);
    if (!local) return;
    event.preventDefault();
    window.location.assign(local);
  }, true);

  var originalOpen = window.open;
  window.open = function (url) {
    var local = toLocalUrl(String(url || ""));
    if (local) {
      window.location.assign(local);
      return null;
    }
    return originalOpen.apply(window, arguments);
  };

  function patchSearch() {
    if (window.RapidSearchSettings) {
      window.RapidSearchSettings.default_domain = window.location.origin;
    }
  }

  if (document.documentElement) rewriteAll(document);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      rewriteAll(document);
      patchSearch();
    });
  } else {
    rewriteAll(document);
    patchSearch();
  }

  if (window.MutationObserver) {
    new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i += 1) {
        var nodes = mutations[i].addedNodes;
        for (var j = 0; j < nodes.length; j += 1) {
          var node = nodes[j];
          if (node.nodeType !== 1) continue;
          if (node.tagName === "A") rewriteAnchor(node);
          else rewriteAll(node);
        }
      }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  setInterval(function () {
    rewriteAll(document);
    patchSearch();
  }, 1000);
})();

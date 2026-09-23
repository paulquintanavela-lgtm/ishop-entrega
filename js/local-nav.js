(function () {
  var LOCAL_CONTENT_VERSION = "20260923-2";
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
      var isCurrentSite = url.origin === window.location.origin;
      if (!SHOP_HOSTS[url.hostname] && !isCurrentSite) return null;
      if (isAssetPath(url.pathname)) return null;
      if (url.pathname.indexOf("/customer_authentication") === 0) return "/account/";
      var pathname = url.pathname;
      var isFile = /\/[^/]+\.[a-z0-9]+$/i.test(pathname);
      if (pathname !== "/" && !isFile && pathname.charAt(pathname.length - 1) !== "/") {
        pathname += "/";
      }
      var params = new URLSearchParams(url.search);
      if (!isFile) {
        params.set("_localv", LOCAL_CONTENT_VERSION);
      }
      var search = params.toString() ? "?" + params.toString() : "";
      return pathname + search + url.hash;
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
    if (
      anchor.matches &&
      anchor.matches(".main-nav__item--toggle > a") &&
      !anchor.dataset.localPrimaryNavigation
    ) {
      anchor.dataset.localPrimaryNavigation = "true";
      anchor.addEventListener("pointerdown", function (event) {
        var destination = toLocalUrl(anchor.getAttribute("href"));
        if (!destination) return;
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === "function") {
          event.stopImmediatePropagation();
        }
        window.location.assign(destination);
      }, true);
    }
  }

  function rewriteAll(root) {
    var scope = root || document;
    if (!scope.querySelectorAll) return;
    var links = scope.querySelectorAll("a[href]");
    for (var i = 0; i < links.length; i += 1) rewriteAnchor(links[i]);
  }

  function simplifyMainMenu() {
    var toggles = document.querySelectorAll("header summary.main-nav__item--toggle");
    for (var i = 0; i < toggles.length; i += 1) {
      var details = toggles[i].parentElement;
      var anchor = toggles[i].querySelector(":scope > a[href]");
      if (!details || details.tagName !== "DETAILS" || !anchor) continue;
      var directLink = anchor.cloneNode(true);
      var icons = directLink.querySelectorAll("svg");
      for (var j = 0; j < icons.length; j += 1) {
        icons[j].remove();
      }
      details.replaceWith(directLink);
    }
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

  function keepPrimaryMenuClickLocal(event) {
    var link = event.target && event.target.closest ? event.target.closest("a[href]") : null;
    var isPrimaryLink = link && link.matches(
      ".main-nav__item--toggle > a, header .main-nav__item--primary"
    );
    if (!isPrimaryLink) {
      var toggle = event.target && event.target.closest
        ? event.target.closest("summary.main-nav__item--toggle")
        : null;
      link = toggle ? toggle.querySelector(":scope > a[href]") : null;
    }
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

  window.addEventListener("click", keepPrimaryMenuClickLocal, true);
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

  if (document.documentElement) {
    simplifyMainMenu();
    rewriteAll(document);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      simplifyMainMenu();
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

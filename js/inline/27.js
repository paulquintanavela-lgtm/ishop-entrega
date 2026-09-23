(function () {
        var customDocumentWrite = function(content) {
          var jquery = null;
    
          if (window.jQuery) {
            jquery = window.jQuery;
          } else if (window.Checkout && window.Checkout.$) {
            jquery = window.Checkout.$;
          }
    
          if (jquery) {
            jquery('body').append(content);
          }
        };
    
        var hasLoggedConversion = function(token) {
          if (token) {
            return document.cookie.indexOf('loggedConversion=' + token) !== -1;
          }
          return false;
        }
    
        var setCookieIfConversion = function(token) {
          if (token) {
            var twoMonthsFromNow = new Date(Date.now());
            twoMonthsFromNow.setMonth(twoMonthsFromNow.getMonth() + 2);
    
            document.cookie = 'loggedConversion=' + token + '; expires=' + twoMonthsFromNow;
          }
        }
    
        var trekkie = window.ShopifyAnalytics.lib = window.trekkie = window.trekkie || [];
        window.ShopifyAnalytics.lib.trekkie = window.trekkie;
        if (trekkie.integrations) {
          return;
        }
        trekkie.methods = [
          'identify',
          'page',
          'ready',
          'track',
          'trackForm',
          'trackLink'
        ];
        trekkie.factory = function(method) {
          return function() {
            var args = Array.prototype.slice.call(arguments);
            args.unshift(method);
            trekkie.push(args);
            if (window.__TREKKIE_SHIM_QUEUE && (method == 'track' || method == 'page')) {
              try {
                window.__TREKKIE_SHIM_QUEUE.push({
                  from: 'trekkie-stub',
                  method: method,
                  args: args.slice(1)
                });
              } catch (e) {
                // no-op
              }
            }
            return trekkie;
          };
        };
        for (var i = 0; i < trekkie.methods.length; i++) {
          var key = trekkie.methods[i];
          trekkie[key] = trekkie.factory(key);
        }
        trekkie.load = function(config) {
          trekkie.config = config || {};
          trekkie.config.initialDocumentCookie = document.cookie;
          var first = document.getElementsByTagName('script')[0];
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.onerror = function(e) {
      var scriptFallback = document.createElement('script');
      scriptFallback.type = 'text/javascript';
      scriptFallback.onerror = function(error) {
              var Monorail = {
          produce: function produce(monorailDomain, schemaId, payload) {
            var currentMs = new Date().getTime();
            var event = {
              schema_id: schemaId,
              payload: payload,
              metadata: {
                event_created_at_ms: currentMs,
                event_sent_at_ms: currentMs
              }
            };
            return Monorail.sendRequest("https://" + monorailDomain + "/v1/produce", JSON.stringify(event));
          },
          sendRequest: function sendRequest(endpointUrl, payload) {
            // Try the sendBeacon API
            if (window && window.navigator && typeof window.navigator.sendBeacon === 'function' && typeof window.Blob === 'function' && !Monorail.isIos12()) {
              var blobData = new window.Blob([payload], {
                type: 'text/plain'
              });
    
              if (window.navigator.sendBeacon(endpointUrl, blobData)) {
                return true;
              } // sendBeacon was not successful
    
            } // XHR beacon
    
            var xhr = new XMLHttpRequest();
    
            try {
              xhr.open('POST', endpointUrl);
              xhr.setRequestHeader('Content-Type', 'text/plain');
              xhr.send(payload);
            } catch (e) {
              console.log(e);
            }
    
            return false;
          },
          isIos12: function isIos12() {
            return window.navigator.userAgent.lastIndexOf('iPhone; CPU iPhone OS 12_') !== -1 || window.navigator.userAgent.lastIndexOf('iPad; CPU OS 12_') !== -1;
          }
        };
        Monorail.produce('monorail-edge.shopifysvc.com',
          'trekkie_storefront_load_errors/1.1',
          {shop_id: 65360888002,
          theme_id: 156106260674,
          app_name: "storefront",
          context_url: window.location.href,
          source_url: "https://ec.tiendasishop.com/cdn/s/trekkie.storefront.d9edb3bdf5942835a042805ba4faf61fecd95cf4.min.js"});
    
      };
      scriptFallback.async = true;
      scriptFallback.src = 'https://ec.tiendasishop.com/cdn/s/trekkie.storefront.d9edb3bdf5942835a042805ba4faf61fecd95cf4.min.js';
      first.parentNode.insertBefore(scriptFallback, first);
    };
    script.async = true;
    script.src = 'https://ec.tiendasishop.com/cdn/s/trekkie.storefront.d9edb3bdf5942835a042805ba4faf61fecd95cf4.min.js';
    first.parentNode.insertBefore(script, first);
    
        };
        trekkie.load(
          {"Trekkie":{"appName":"storefront","development":false,"defaultAttributes":{"shopId":65360888002,"isMerchantRequest":null,"themeId":156106260674,"themeCityHash":"1254660166671251169","contentLanguage":"es","currency":"USD","eventMetadataId":"9cc86739-b27b-498b-ba9b-8a8dea9fea54"},"isServerSideCookieWritingEnabled":true,"monorailRegion":"shop_domain"},"Session Attribution":{},"S2S":{"facebookCapiEnabled":true,"source":"trekkie-storefront-renderer","apiClientId":580111}}
        );
    
        var loaded = false;
        trekkie.ready(function() {
          if (loaded) return;
          loaded = true;
    
          window.ShopifyAnalytics.lib = window.trekkie;
    
          var originalDocumentWrite = document.write;
          document.write = customDocumentWrite;
          try { window.ShopifyAnalytics.merchantGoogleAnalytics.call(this); } catch(error) {};
          document.write = originalDocumentWrite;
    
          var match = window.location.pathname.match(/checkouts\/(.+)\/(thank_you|post_purchase)/)
          var token = match? match[1]: undefined;
          if (!hasLoggedConversion(token)) {
            setCookieIfConversion(token);
            
          }
        });
    
        window.ShopifyAnalytics.lib.page(null,{"pageType":"home","requestId":"f1e54b3c-be8f-41c3-a074-f78c40f9fd7c-1790107948","shopifyEmitted":true});
    
        var eventsListenerScript = document.createElement('script');
        eventsListenerScript.async = true;
        eventsListenerScript.src = "https://ec.tiendasishop.com/cdn/shopifycloud/storefront/assets/shop_events_listener-4e26a9ce.js";
        document.getElementsByTagName('head')[0].appendChild(eventsListenerScript);
    })();

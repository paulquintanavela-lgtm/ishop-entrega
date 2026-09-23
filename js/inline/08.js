(function() {
      var isLoaded = false;
      function asyncLoad() {
        if (isLoaded) return;
        isLoaded = true;
        var urls = ["https:\/\/static2.rapidsearch.dev\/resultpage.js?shop=ishop-ecuador.myshopify.com","https:\/\/cdn.rebuyengine.com\/onsite\/js\/rebuy.js?shop=ishop-ecuador.myshopify.com"];
        for (var i = 0; i < urls.length; i++) {
          var s = document.createElement('script');
          s.type = 'text/javascript';
          s.async = true;
          s.src = urls[i];
          var x = document.getElementsByTagName('script')[0];
          x.parentNode.insertBefore(s, x);
        }
      };
      if(window.attachEvent) {
        window.attachEvent('onload', asyncLoad);
      } else {
        window.addEventListener('load', asyncLoad, false);
      }
    })();

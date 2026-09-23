(function () {
        try {
          const url = "https://cdn.shopify.com/extensions/01a0c8cf-02de-7422-8886-72521b4cba6f/rapid-search-415/assets/resultpage.js?shop=ishop-ecuador.myshopify.com";
          const match = url.match(/^(.*\/assets\/)/);
          
          if (match) {
            window.RapidSearchShopifyExtensionsCdnBaseUrl = match[1];
          }
        } catch (error) {
          console.error('Error setting Shopify CDN base URL:', error);
        }
      })();

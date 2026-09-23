window.theme = {
          info: {
            name: 'Enterprise',
            version: '1.6.2'
          },
          mediaQueries: {
            sm: '(min-width: 600px)',
            md: '(min-width: 769px)',
            lg: '(min-width: 1024px)',
            xl: '(min-width: 1280px)',
            xxl: '(min-width: 1536px)',
            portrait: '(orientation: portrait)'
          },
          device: {
            hasTouch: window.matchMedia('(any-pointer: coarse)').matches,
            hasHover: window.matchMedia('(hover: hover)').matches
          },
          routes: {
            cart: '/cart',
            cartAdd: '/cart/add',
            cartChange: '/cart/change',
            cartUpdate: '/cart/update',
            predictiveSearch: '/search/suggest'
          },
          settings: {
            moneyWithCurrencyFormat: "${{amount}} USD",
            pSearchLimit: 10,
            pSearchLimitScope: 'each',
            pSearchIncludeSkus: true,
            pSearchIncludeTags: true,
            sliderItemsPerNav: 'page',
            
            vibrateOnATC: false,
            compareToggle: "toggle_on",
            compareShowEmptyMetafields: true,
            blendProductImages: false,
            externalLinksNewTab: true,
            afterAtc: "drawer",
            cartType: "drawer"
          },
          strings: {
            addCartNote: 'Añadir observaciones del pedido',
            editCartNote: 'Editar observaciones del pedido',
            cartError: 'Se ha producido un error al actualizar el carrito. Inténtelo nuevamente.',
            cartQtyError: 'Solo puede añadir [quantity] unidades de este artículo al carrito.',
            cartTermsConfirmation: 'Tiene que aceptar los términos y condiciones antes de continuar.',
            imageAvailable: 'La imagen [index] ya está disponible en la vista de galería',
            veryLowStock: 'Últimas unidades disponibles',
            lowStock: 'Poca disponibilidad',
            inStock: 'Disponibles',
            noStock: 'Sin stock',
            noVariant: 'Sin stock',
            noSelectedVariant: 'Has una elección',
            onlyXLeft: '[quantity] disponibles',
            awaitingSale: 'Este producto no está disponible para comprar todavía.',
            shippingCalculator: {
              singleRate: 'Hay una tarifa de envío para este destino:',
              multipleRates: 'Hay varias tarifas de envío para este destino:',
              noRates: 'No hacemos envíos a este destino.'
            },
            viewDetails: 'Ver modelos',
            compare: {
              limit: 'Solo puede añadir un máximo de [quantity] productos para comparar.',
              more: 'Seleccione otro producto para comparar.',
              empty: 'Seleccione al menos dos productos para comparar.',
              continue: 'Cierre para continuar.'
            },
            discountCopyFail: 'No se ha podido copiar el código al portapapeles. Es posible que el navegador no admita esta función.',
            articleReadTime: '[x] minutos de lectura',
            quickNav: {
              button_standard: 'Buscar',
              show_products_none: 'No hay productos :(',
              button_one: 'Mostrar [quantity] producto',
              button_other: 'Mostrar [quantity] productos',
            },
          },
          scripts: {
            cartItems: 'https://ec.tiendasishop.com/cdn/shop/t/19/assets/cart-items.js?v=174056483318147133191789000855',
            countryProvinceSelector: 'https://ec.tiendasishop.com/cdn/shop/t/19/assets/country-province-selector.js?v=24158546944577672431789000855',
            shippingCalculator: 'https://ec.tiendasishop.com/cdn/shop/t/19/assets/shipping-calculator.js?v=31725526838375758301789000854'
          }
        };
    
        // Save product ID to localStorage, for use in the 'Recently viewed products' section.

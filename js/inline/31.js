(async function () {
        let bsure_metafield = {};
        try {
          bsure_metafield = JSON.parse('{"tz":"America/Guayaquil"}' || '{}');
        } catch (e) {
          console.error('Failed to parse bsure metafield:', e);
        }
        const bsure_tzDict = bsure_metafield.tz ? { timeZone: bsure_metafield.tz } : {};
    
        const bsure_options = {
          year: 'numeric',
          month: 'numeric',
          day: 'numeric',
          hour: 'numeric',
          minute: 'numeric',
          second: 'numeric',
          hourCycle: 'h23',
          weekday: 'short',
          timeZoneName: 'shortOffset',
          ...bsure_tzDict,
        };
    
        const bsure_date = new Date();
        const bsure_dt_attribute = new Intl.DateTimeFormat('en-US', bsure_options).format(bsure_date);
    
        // Get timezone
        let bsure_timezone = '';
        try {
          bsure_timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        } catch (e) {
          console.log('Could not get timezone:', e);
        }
    
        // Get country code
        let bsure_country = '';
        let bsure_rootPath = '/';
    
        try {
          bsure_rootPath = window.Shopify.routes.root;
        } catch (e) {
          console.log(e);
        }
    
        try {
          bsure_country = window.Shopify.country || '';
        } catch (e) {
          console.log('Could not get country from Shopify global:', e);
        }
    
        const bsure_postAttribute = async (value, endpoint) => {
          try {
            await fetch(`${bsure_rootPath}${endpoint}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ attributes: { 'bsure-attribute': value } }),
            });
          } catch (e) {
            console.error(e);
          }
        };
    
        const bsure_buildAttribute = (country) => {
          // Build combined attribute string: "Time | XX (Country Code) | TimeZone"
          let bsure_combined_attribute = bsure_dt_attribute;
    
          if (country) {
            bsure_combined_attribute += ` | c:${country}`;
          }
    
          if (bsure_timezone) {
            bsure_combined_attribute += ` | tz:${bsure_timezone}`;
          }
          return bsure_combined_attribute;
        };
    
        // Write immediately so date/time rules don't depend on GeoIP call latency.
        const bsure_initial_attribute = bsure_buildAttribute(bsure_country);
        console.log(bsure_initial_attribute);
        const bsure_initial_post = bsure_postAttribute(bsure_initial_attribute, 'cart.js');
    
        try {
          // Try Shopify's browsing context suggestions API afterwards and refine country if needed.
          const response = await fetch(`${bsure_rootPath}browsing_context_suggestions.json?country[enabled]=true`);
    
          if (response.ok) {
            const data = await response.json();
            const detected_country = data?.detected_values?.country?.handle || '';
            if (detected_country && detected_country !== bsure_country) {
              await bsure_initial_post;
              const bsure_updated_attribute = bsure_buildAttribute(detected_country);
              console.log(bsure_updated_attribute);
              await bsure_postAttribute(bsure_updated_attribute, 'cart/update.js');
            }
          }
        } catch (e) {
          console.log('Browsing context API unavailable:', e);
        }
      })();

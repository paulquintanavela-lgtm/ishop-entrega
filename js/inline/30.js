var klaviyo = klaviyo || [];
    klaviyo.init({
      account: "WS2sew",
      list:"TbGUNm",
      platform: "shopify"
    });
    klaviyo.enable("backinstock",{ 
    trigger: {
      product_page_text: "Notifícame cuando esté disponible",
      product_page_class: "button",
      product_page_text_align: "center",
      product_page_margin: "0px",
      replace_anchor: false
    },
    modal: {
     headline: "{product_name}",
     body_content: "Regístrate para recibir una notificación cuando este artículo esté en stock.",
     email_field_label: "Correo electrónico",
     button_label: "Notifícame cuando esté disponible",
     newsletter_subscribe_label: "Quiero recibir otras promociones y ofertas.", 
     subscription_success_label: "¡Estás registrado! Te avisaremos cuando esté disponible.",
     footer_content: '',
     drop_background_color: "#000",
     background_color: "#fff",
     text_color: "#222",
     button_text_color: "#fff",
     button_background_color: "#f68025",
     close_button_color: "#ccc",
     error_background_color: "#fcd6d7",
     error_text_color: "#C72E2F",
     success_background_color: "#d3efcd",
     success_text_color: "#1B9500"
    }
    });

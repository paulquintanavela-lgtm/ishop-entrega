import { createChat } from "https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js";

const DEFAULT_CHAT_WEBHOOK_URL =
  "http://localhost:5678/webhook/7b30dce3-a9c0-4e49-b25c-3d2f6a71c980/chat";
const CHAT_OPEN_KEY = "ishop-chat/open";
const CHATWOOT_CONFIG_URL = "/chatbot/widget/chatwoot-config.json";
const WIDGET_STYLES = "/chatbot/widget/chatbot-widget.css?v=20260923-cw1";

const QUICK_ACTIONS = [
  {
    label: "Elegir un equipo",
    message: "Quiero que me recomiendes un equipo según mi uso y presupuesto.",
  },
  {
    label: "Quiero comprar",
    message:
      "Quiero comprar. Si ya elegimos un producto, indícame el enlace y los siguientes pasos.",
  },
  {
    label: "Necesito soporte",
    message: "Necesito ayuda con soporte técnico, garantía o reparación.",
  },
  {
    label: "Hablar con un asesor",
    message: "Quiero hablar con un asesor humano en esta misma conversación.",
  },
];

function addStylesheet(href) {
  if (document.querySelector(`link[href="${href}"]`)) {
    return;
  }

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  document.head.append(link);
}

async function loadWidgetConfig() {
  try {
    const response = await fetch(CHATWOOT_CONFIG_URL, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch {
    return null;
  }
}

function initializeChatwoot(config) {
  addStylesheet(WIDGET_STYLES);

  window.chatwootSettings = {
    hideMessageBubble: false,
    position: "right",
    locale: "es",
    type: "expanded_bubble",
    launcherTitle: "¿Cómo podemos ayudarte?",
    darkMode: "light",
  };

  const baseUrl = config.baseUrl || "http://localhost:3000";
  const script = document.createElement("script");
  script.src = `${baseUrl}/packs/js/sdk.js`;
  script.async = true;
  script.defer = true;
  script.onload = () => {
    window.chatwootSDK?.run({
      websiteToken: config.websiteToken,
      baseUrl,
    });
  };
  document.head.append(script);

  window.addEventListener("chatwoot:ready", () => {
    if (localStorage.getItem(CHAT_OPEN_KEY) === "true") {
      window.$chatwoot?.toggle("open");
    }
  });
  window.addEventListener("chatwoot:opened", () => {
    localStorage.setItem(CHAT_OPEN_KEY, "true");
  });
  window.addEventListener("chatwoot:closed", () => {
    localStorage.setItem(CHAT_OPEN_KEY, "false");
  });
}

function setTextAreaValue(textarea, value) {
  const descriptor = Object.getOwnPropertyDescriptor(
    HTMLTextAreaElement.prototype,
    "value",
  );
  descriptor?.set?.call(textarea, value);
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}

function sendQuickMessage(message) {
  const textarea = document.querySelector("#n8n-chat textarea");
  if (!textarea) {
    return;
  }

  textarea.focus();
  setTextAreaValue(textarea, message);
  window.setTimeout(() => {
    const sendButton = document.querySelector(
      "#n8n-chat .chat-input-send-button",
    );
    if (sendButton && !sendButton.disabled) {
      sendButton.click();
    }
  }, 60);
}

function enhanceChat() {
  const root = document.querySelector("#n8n-chat");
  const wrapper = root?.querySelector(".chat-window-wrapper");
  const chatWindow = root?.querySelector(".chat-window");
  const header = root?.querySelector(".chat-header");
  const footer = root?.querySelector(".chat-footer");
  const toggle = root?.querySelector(".chat-window-toggle");
  if (!wrapper || !chatWindow || !header || !footer || !toggle) {
    return false;
  }

  toggle.setAttribute("role", "button");
  toggle.setAttribute("tabindex", "0");
  toggle.setAttribute("aria-label", "Abrir asistente iShop");

  if (!header.querySelector(".ishop-chat-status")) {
    const status = document.createElement("div");
    status.className = "ishop-chat-status";
    status.innerHTML =
      '<span aria-hidden="true"></span>Asistente virtual disponible';
    header.append(status);
  }

  if (!wrapper.querySelector(".ishop-chat-actions")) {
    const actions = document.createElement("div");
    actions.className = "ishop-chat-actions";
    actions.setAttribute("aria-label", "Acciones rápidas");

    QUICK_ACTIONS.forEach(({ label, message }) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.addEventListener("click", () => sendQuickMessage(message));
      actions.append(button);
    });

    footer.before(actions);
  }

  if (!wrapper.dataset.ishopStateBound) {
    wrapper.dataset.ishopStateBound = "true";
    const saveWindowState = () => {
      const isOpen = chatWindow.style.display !== "none";
      localStorage.setItem(CHAT_OPEN_KEY, String(isOpen));
      toggle.setAttribute(
        "aria-label",
        isOpen ? "Cerrar asistente iShop" : "Abrir asistente iShop",
      );
    };
    new MutationObserver(saveWindowState).observe(chatWindow, {
      attributes: true,
      attributeFilter: ["style"],
    });
    toggle.addEventListener("click", () => {
      window.setTimeout(saveWindowState);
    });
    toggle.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle.click();
      }
    });

    if (
      localStorage.getItem(CHAT_OPEN_KEY) === "true" &&
      chatWindow.style.display === "none"
    ) {
      toggle.click();
    }
  }

  return true;
}

function installEnhancements() {
  if (enhanceChat()) {
    return;
  }
  const observer = new MutationObserver(() => {
    if (enhanceChat()) {
      observer.disconnect();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

function initializeN8nChat(webhookUrl) {
  if (document.querySelector("#n8n-chat")) {
    return;
  }

  addStylesheet("https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css");
  addStylesheet(WIDGET_STYLES);

  const target = document.createElement("div");
  target.id = "n8n-chat";
  document.body.append(target);

  createChat({
    webhookUrl,
    target: "#n8n-chat",
    mode: "window",
    chatInputKey: "chatInput",
    chatSessionKey: "sessionId",
    loadPreviousSession: true,
    showWelcomeScreen: false,
    defaultLanguage: "es",
    initialMessages: [
      "Hola, soy el asistente virtual de demostración de iShop.",
      "Puedo ayudarte con productos, compras, envíos, garantía y servicio técnico.",
    ],
    metadata: {
      source: "ishop-local",
    },
    i18n: {
      es: {
        title: "¿Cómo podemos ayudarte?",
        subtitle: "Compras, productos y soporte iShop",
        footer: "Asistente virtual de demostración",
        getStarted: "Nueva conversación",
        inputPlaceholder: "Cuéntanos qué necesitas…",
        closeButtonTooltip: "Cerrar chat",
      },
    },
  });

  installEnhancements();
}

async function initializeChat() {
  const config = await loadWidgetConfig();
  if (config?.websiteToken) {
    initializeChatwoot(config);
    return;
  }
  initializeN8nChat(config?.n8nWebhookUrl || DEFAULT_CHAT_WEBHOOK_URL);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeChat, { once: true });
} else {
  initializeChat();
}

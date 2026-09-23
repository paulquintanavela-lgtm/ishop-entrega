import { createChat } from "https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js";

const CHAT_WEBHOOK_URL =
  "http://localhost:5678/webhook/7b30dce3-a9c0-4e49-b25c-3d2f6a71c980/chat";

function addStylesheet(href) {
  if (document.querySelector(`link[href="${href}"]`)) {
    return;
  }

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  document.head.append(link);
}

function initializeChat() {
  if (document.querySelector("#n8n-chat")) {
    return;
  }

  addStylesheet("https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css");
  addStylesheet("/chatbot/widget/chatbot-widget.css");

  const target = document.createElement("div");
  target.id = "n8n-chat";
  document.body.append(target);

  createChat({
    webhookUrl: CHAT_WEBHOOK_URL,
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
        title: "Asistente iShop",
        subtitle: "Consulta productos, ventas y servicio posventa",
        footer: "Demostración con IA y RAG",
        getStarted: "Nueva conversación",
        inputPlaceholder: "Escribe tu pregunta…",
        closeButtonTooltip: "Cerrar chat",
      },
    },
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeChat, { once: true });
} else {
  initializeChat();
}

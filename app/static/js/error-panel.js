// Painel com os arquivos que falharam e o motivo (SCRUM-42).

import { h, icon, VERBS } from "./ui.js";

export function failedItems(batch) {
  return batch.items.filter((item) => item.status === "failed");
}

export function hideErrors(container) {
  container.replaceChildren();
}

export function showErrors(container, batch) {
  const failed = failedItems(batch);
  hideErrors(container);
  if (failed.length === 0) return;
  const close = h(
    "button",
    { type: "button", class: "link", onclick: () => hideErrors(container) },
    "Fechar", icon("close")
  );
  container.append(h(
    "section", { class: "error-panel", role: "alert" },
    h(
      "header", {}, icon("warning"),
      h("strong", {}, VERBS[batch.kind].notDoneMany(failed.length)), close
    ),
    h("ul", {}, ...failed.map((item) => h(
      "li", {}, h("strong", {}, item.name), h("span", {}, item.error)
    )))
  ));
}

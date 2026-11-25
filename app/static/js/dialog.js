// Diálogo de confirmação (SCRUM-41).

import { button, h, icon, folderName, folderTrail, joinNames } from "./ui.js";
import { fileCount, number, VERBS } from "./ui.js";

const MAX_NAMES = 8;

// Resolve true se confirmado. onConfirm roda dentro do clique (necessário
// para pedir permissões); se lançar erro, o diálogo continua aberto.
export function confirmDialog({ title, body, confirmLabel, danger, onConfirm }) {
  return new Promise((resolve) => {
    const error = h("p", { class: "error", role: "alert", hidden: true });
    const cancel = button("Cancelar", () => dialog.close("cancel"));
    const confirm = button(
      confirmLabel || "Confirmar", accept, danger ? "danger" : "primary"
    );
    const heading = h("h2", { id: "dialog-title" }, title);
    const dialog = h(
      "dialog", { class: "modal", "aria-labelledby": "dialog-title" },
      heading, ...body, error,
      h("div", { class: "modal-actions" }, cancel, confirm)
    );

    async function accept() {
      confirm.disabled = true;
      try {
        if (onConfirm) await onConfirm();
        dialog.close("confirm");
      } catch (failure) {
        error.textContent = failure.message;
        error.hidden = false;
      } finally {
        confirm.disabled = false;
      }
    }

    dialog.addEventListener("close", () => {
      dialog.remove();
      resolve(dialog.returnValue === "confirm");
    });
    document.body.append(dialog);
    dialog.showModal();
    (danger ? cancel : confirm).focus();
  });
}

function namesList(items) {
  const rows = items.slice(0, MAX_NAMES).map((item) => {
    const renamed = item.target_name && item.target_name !== item.name;
    return h("li", {}, renamed ? `${item.name} → ${item.target_name}` : item.name);
  });
  const rest = items.length - rows.length;
  if (rest > 0) rows.push(h("li", { class: "muted" }, `e mais ${number(rest)}`));
  return h("ul", { class: "modal-names" }, ...rows);
}

function fromTo(plan) {
  const column = (label, text) => h(
    "div", {}, h("span", { class: "muted" }, label), h("strong", {}, text)
  );
  return h(
    "div", { class: "from-to" },
    column("De", plan.sources.map(folderTrail).join(", ")),
    ...(plan.destination
      ? [icon("arrow"), column("Para", folderTrail(plan.destination))]
      : [])
  );
}

const NOTES = {
  copy: "Os arquivos originais continuam na origem.",
  move: "Os arquivos são copiados para o destino e só depois removidos " +
    "da origem.",
  delete: "A exclusão é definitiva: os arquivos não vão para a lixeira.",
};

export function confirmBatch(plan, onConfirm) {
  const { kind, sources, destination, items, progress } = plan;
  const from = joinNames(sources.map(folderName));
  const to = destination ? ` para ${folderName(destination)}` : "";
  return confirmDialog({
    title: `${VERBS[kind].infinitive} ${fileCount(progress.total)} ` +
      `de ${from}${to}?`,
    body: [
      fromTo(plan),
      namesList(items),
      h("p", { class: "muted" }, NOTES[kind]),
    ],
    confirmLabel: kind === "delete" ? "Deletar" : "Confirmar",
    danger: kind === "delete",
    onConfirm,
  });
}

// Barra de progresso de um lote em execução.

import { h, number, VERBS } from "./ui.js";

export function progressBar(container, kind) {
  const label = h("span", {});
  const bar = h("progress", { max: 1, value: 0 });
  container.replaceChildren(label, bar);
  container.hidden = false;
  return {
    update(current, total) {
      label.textContent =
        `${VERBS[kind].gerund}… ${number(current)} de ${number(total)}`;
      bar.max = total;
      bar.value = current - 1;
    },
    remove() {
      container.replaceChildren();
      container.hidden = true;
    },
  };
}

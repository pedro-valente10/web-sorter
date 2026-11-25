// Abas da tela principal. Cada aba fica em memória, então trocar de aba
// não perde as pastas escolhidas nem interrompe uma operação.

import { initDecide } from "./decide.js";
import { initExplore } from "./explore.js";
import { initHistory, refreshHistory } from "./history.js";
import { initOrganize } from "./organize.js";

const DEFAULT_TAB = "organizar";
const panels = [...document.querySelectorAll("[data-panel]")];
const links = [...document.querySelectorAll("[data-tab]")];

function showTab() {
  const wanted = window.location.hash.slice(1);
  const tab = panels.some((p) => p.dataset.panel === wanted)
    ? wanted : DEFAULT_TAB;
  for (const panel of panels) panel.hidden = panel.dataset.panel !== tab;
  for (const link of links) {
    if (link.dataset.tab === tab) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (tab === "historico") refreshHistory();
}

window.addEventListener("hashchange", showTab);
initOrganize();
initExplore();
initDecide();
initHistory();
showTab();

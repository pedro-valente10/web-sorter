// Aba "Decidir arquivo a arquivo": decisões salvas na conta do usuário.

import { api } from "./api.js";
import { confirmDialog } from "./dialog.js";
import {
  copyFile, entryNames, isSupported, listEntries, pickFolder, removeFile,
  UNSUPPORTED,
} from "./fs.js";
import {
  buildPreview, LazyLoader, placeholder, releaseUrls,
} from "./previews.js";
import { button, dateTime, fileCount, h, plural, setStatus } from "./ui.js";

const $ = (id) => document.getElementById(id);

const el = {
  pick: $("decide-pick"),
  status: $("decide-status"),
  recent: $("recent"),
  recentList: $("recent-list"),
  panel: $("decide-panel"),
  destinationForm: $("destination-form"),
  destinationName: $("destination-name"),
  filter: $("decide-filter"),
  apply: $("decide-apply"),
  progress: $("decide-summary"),
  grid: $("decide-grid"),
};

const state = {
  directory: null,
  session: null,
  decisions: new Map(), // nome do arquivo -> decisão vinda do servidor
  cards: new Map(), // nome do arquivo -> card
  urls: [],
};

const sessionUrl = (path) => `/sessions/${state.session.id}${path}`;

// Decisões já aplicadas (arquivo movido/excluído) não valem para um
// arquivo de mesmo nome que apareça de novo na pasta.
function activeDecision(name) {
  const decision = state.decisions.get(name);
  if (!decision) return null;
  if (decision.applied && decision.action !== "keep") return null;
  return decision;
}

// ---------- cards ----------

const lazy = new LazyLoader(async (root) => {
  const card = state.cards.get(root.dataset.name);
  if (!card) return;
  const file = await card.handle.getFile();
  const preview = await buildPreview(card.name, file, state.urls);
  if (preview) card.thumb.replaceChildren(preview);
});

function buildCard({ name, handle }) {
  const thumb = h("div", { class: "thumb" }, placeholder(name));
  const badge = h("p", { class: "detail muted" });
  const select = h("select", {
    "aria-label": `Mover ${name} para`,
    onchange: () => select.value && decide(name, "move", select.value),
  });
  const undo = button("Desfazer", () => undoDecision(name));
  const root = h(
    "article", { class: "tile decision" },
    thumb, h("strong", { class: "name", title: name }, name), badge, select,
    h(
      "div", { class: "tile-actions" },
      button("Excluir", () => decide(name, "delete"), "danger"),
      button("Manter", () => decide(name, "keep")),
      undo
    )
  );
  root.dataset.name = name;
  return { name, handle, root, thumb, badge, select, undo };
}

function matchesFilter(decision) {
  const filter = el.filter.value;
  if (filter === "all") return true;
  if (filter === "pending") return !decision;
  return Boolean(decision) && decision.action === filter;
}

function describe(decision) {
  if (!decision) return "Sem decisão";
  const labels = {
    move: `Mover para ${decision.destination}`,
    delete: "Excluir",
    keep: "Manter",
  };
  return labels[decision.action] + (decision.applied ? " (aplicado)" : "");
}

function renderCard(card) {
  const decision = activeDecision(card.name);
  card.root.dataset.state = decision ? decision.action : "pending";
  card.select.value =
    decision && decision.action === "move" ? decision.destination : "";
  card.undo.hidden = !decision || decision.applied;
  card.badge.textContent = describe(decision);
  card.root.hidden = !matchesFilter(decision);
}

function renderAll() {
  state.cards.forEach(renderCard);
}

function renderDestinations() {
  for (const card of state.cards.values()) {
    card.select.replaceChildren(
      new Option("Mover para…", ""),
      ...state.session.destinations.map((name) => new Option(name, name))
    );
    renderCard(card);
  }
}

// ---------- pasta e sessão ----------

async function scanFolder() {
  const { files } = await listEntries(state.directory);
  lazy.reset();
  releaseUrls(state.urls);
  state.cards = new Map(files.map((file) => [file.name, buildCard(file)]));
  const roots = [...state.cards.values()].map((card) => card.root);
  el.grid.replaceChildren(...(roots.length > 0
    ? roots : [h("p", { class: "empty" }, "Pasta vazia.")]));
  roots.forEach((root) => lazy.observe(root));
}

async function openFolder() {
  const handle = await pickFolder("readwrite");
  if (!handle) return;
  setStatus(el.status, "Carregando…");
  const data = await api("POST", "/sessions", { folder_name: handle.name });
  state.directory = handle;
  state.session = data.session;
  state.decisions = new Map(data.decisions.map((d) => [d.path, d]));
  await scanFolder();
  el.panel.hidden = false;
  renderDestinations();
  await refreshSummary();
  await loadRecentSessions();
  reportResume(data.decisions);
}

function reportResume(decisions) {
  const missing = decisions.filter(
    (d) => !d.applied && !state.cards.has(d.path)
  ).length;
  let message = `Pasta "${state.session.folder_name}": ` +
    `${fileCount(state.cards.size)}.`;
  if (decisions.length > 0) message += " Decisões anteriores restauradas.";
  if (missing > 0) {
    message += ` ${plural(missing, "decisão é", "decisões são")} ` +
      "de arquivos que não estão mais aqui.";
  }
  setStatus(el.status, message);
}

async function loadRecentSessions() {
  const data = await api("GET", "/sessions").catch(() => ({ sessions: [] }));
  el.recentList.replaceChildren(...data.sessions.map((session) => h(
    "li", {}, h("strong", {}, session.folder_name), " ",
    h("span", { class: "muted" }, dateTime(session.updated_at))
  )));
  el.recent.hidden = data.sessions.length === 0;
}

// ---------- decisões ----------

async function decide(name, action, destination) {
  await guarded(async () => {
    const body = { path: name, action };
    if (destination) body.destination = destination;
    const decision = await api("PUT", sessionUrl("/decisions"), body);
    state.decisions.set(name, decision);
    await refreshSummary();
  });
}

async function undoDecision(name) {
  await guarded(async () => {
    await api("DELETE", sessionUrl("/decisions"), { path: name });
    state.decisions.delete(name);
    await refreshSummary();
  });
}

async function addDestination(event) {
  event.preventDefault();
  await guarded(async () => {
    state.session = await api("POST", sessionUrl("/destinations"), {
      name: el.destinationName.value,
    });
    el.destinationName.value = "";
    renderDestinations();
  });
}

async function refreshSummary() {
  const summary = await api("GET", sessionUrl("/summary"));
  const waiting = [...state.cards.keys()]
    .filter((name) => !activeDecision(name)).length;
  el.progress.textContent =
    `Sem decisão: ${waiting} · Mover: ${summary.by_action.move} · ` +
    `Excluir: ${summary.by_action.delete} · ` +
    `Manter: ${summary.by_action.keep} · ` +
    `Já aplicadas: ${summary.applied}`;
  renderAll();
}

// ---------- aplicar na pasta ----------

async function applyOne(decision) {
  if (decision.action === "keep") return;
  if (decision.action === "move") {
    const target = await state.directory.getDirectoryHandle(
      decision.destination, { create: true }
    );
    const { name } = await api("POST", "/target-name", {
      name: decision.path, taken_names: await entryNames(target),
    });
    await copyFile(state.directory, decision.path, target, name);
  }
  await removeFile(state.directory, decision.path);
}

async function applyDecisions() {
  const todo = [...state.decisions.values()].filter(
    (d) => !d.applied && state.cards.has(d.path)
  );
  if (todo.length === 0) {
    setStatus(el.status, "Não há decisões para aplicar.");
    return;
  }
  const deletions = todo.filter((d) => d.action === "delete").length;
  const confirmed = await confirmDialog({
    title: `Aplicar ${plural(todo.length, "decisão", "decisões")} em ` +
      `${state.session.folder_name}?`,
    body: [h("p", { class: "muted" }, deletions === 0
      ? "Nenhum arquivo será excluído."
      : `${fileCount(deletions)} ` +
        `${deletions === 1 ? "será excluído" : "serão excluídos"} ` +
        "definitivamente, sem passar pela lixeira.")],
    confirmLabel: "Aplicar",
    danger: deletions > 0,
  });
  if (!confirmed) return;

  let done = 0;
  const failures = [];
  el.apply.disabled = true;
  for (const decision of todo) {
    try {
      await applyOne(decision);
      const applied = await api("POST", sessionUrl("/decisions/applied"), {
        path: decision.path,
      });
      state.decisions.set(decision.path, applied);
      done += 1;
    } catch (error) {
      failures.push(decision.path);
    }
  }
  el.apply.disabled = false;
  await scanFolder();
  renderDestinations();
  await refreshSummary();
  const result = plural(done, "decisão aplicada", "decisões aplicadas");
  setStatus(el.status, failures.length === 0 ? `${result}.`
    : `${result}. Não foi possível aplicar: ${failures.join(", ")}.`,
  failures.length > 0);
}

async function guarded(action) {
  try {
    await action();
  } catch (error) {
    setStatus(el.status, error.message, true);
    renderAll();
  }
}

// ---------- eventos ----------

export function initDecide() {
  el.pick.addEventListener("click", () => guarded(openFolder));
  el.destinationForm.addEventListener("submit", addDestination);
  el.filter.addEventListener("change", renderAll);
  el.apply.addEventListener("click", () => guarded(applyDecisions));
  if (!isSupported()) setStatus(el.status, UNSUPPORTED, true);
  loadRecentSessions();
}

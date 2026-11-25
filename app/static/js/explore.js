// Aba "Explorar pasta (grade)" (SCRUM-40, SCRUM-41 e SCRUM-42).

import { isBusy, planBatch, startBatch } from "./batch-runner.js";
import { confirmBatch } from "./dialog.js";
import { failedItems, hideErrors, showErrors } from "./error-panel.js";
import {
  describeError, ensurePermission, entryNames, isSupported, listEntries,
  pickFolder, UNSUPPORTED,
} from "./fs.js";
import {
  buildPreview, LazyLoader, placeholder, releaseUrls,
} from "./previews.js";
import { progressBar } from "./progress.js";
import {
  batchResult, bytes, h, icon, number, plural, setStatus, VERBS,
} from "./ui.js";

const $ = (id) => document.getElementById(id);

const el = {
  pick: $("explore-pick"),
  count: $("explore-count"),
  all: $("explore-all"),
  none: $("explore-none"),
  move: $("explore-move"),
  remove: $("explore-delete"),
  status: $("explore-status"),
  progress: $("explore-progress"),
  errors: $("explore-errors"),
  trail: $("explore-trail"),
  grid: $("explore-grid"),
};

const state = {
  trail: [], // da raiz escolhida até a pasta atual
  files: new Map(), // nome -> { handle, card, detail }
  selected: new Set(),
  failed: new Map(), // nome -> aviso, como "Não movido"
  anchor: null,
  urls: [],
};

const root = () => state.trail[0];
const current = () => state.trail.at(-1);
const pathOf = (handles) => handles.map((handle) => handle.name).join("/");

// ---------- listagem ----------

const lazy = new LazyLoader(async (card) => {
  const { name, kind } = card.dataset;
  if (kind === "folder") {
    const handle = await current().getDirectoryHandle(name);
    const count = (await entryNames(handle)).length;
    card.querySelector(".detail").textContent = plural(count, "item", "itens");
    return;
  }
  const entry = state.files.get(name);
  if (!entry) return;
  const file = await entry.handle.getFile();
  entry.size = bytes(file.size);
  paint(name);
  const preview = await buildPreview(name, file, state.urls);
  if (preview) card.querySelector(".thumb").replaceChildren(preview);
});

function folderCard({ name, handle }) {
  const card = h(
    "button",
    { type: "button", class: "tile folder", onclick: act(() => enter(handle)) },
    h("span", { class: "thumb" }, icon("folder")),
    h("strong", { class: "name", title: name }, name),
    h("span", { class: "detail muted" })
  );
  card.dataset.name = name;
  card.dataset.kind = "folder";
  return card;
}

function fileCard({ name }) {
  const card = h(
    "button",
    {
      type: "button", class: "tile", "aria-pressed": "false",
      onclick: (event) => toggle(name, event.shiftKey),
    },
    h("span", { class: "mark" }, icon("check")),
    h("span", { class: "thumb" }, placeholder(name)),
    h("strong", { class: "name", title: name }, name),
    h("span", { class: "detail muted" })
  );
  card.dataset.name = name;
  card.dataset.kind = "file";
  return card;
}

async function load() {
  const { folders, files } = await listEntries(current());
  lazy.reset();
  releaseUrls(state.urls);
  state.files.clear();
  const cards = folders.map(folderCard);
  for (const file of files) {
    const card = fileCard(file);
    state.files.set(file.name, { handle: file.handle, card, size: "" });
    cards.push(card);
  }
  keepExisting(state.selected);
  keepExisting(state.failed);
  el.grid.replaceChildren(...(cards.length > 0
    ? cards : [h("p", { class: "empty" }, "Pasta vazia.")]));
  cards.forEach((card) => lazy.observe(card));
  render();
}

function keepExisting(collection) {
  for (const name of [...collection.keys()]) {
    if (!state.files.has(name)) collection.delete(name);
  }
}

async function goTo(trail) {
  const previous = state.trail;
  state.trail = trail;
  state.selected.clear();
  state.failed.clear();
  state.anchor = null;
  hideErrors(el.errors);
  setStatus(el.status, "");
  try {
    await load();
  } catch (error) {
    state.trail = previous;
    throw error;
  }
}

const enter = (handle) => goTo([...state.trail, handle]);

// ---------- seleção ----------

function toggle(name, range) {
  if (isBusy()) return;
  const names = [...state.files.keys()];
  if (range && state.files.has(state.anchor)) {
    const ends = [names.indexOf(state.anchor), names.indexOf(name)];
    names.slice(Math.min(...ends), Math.max(...ends) + 1)
      .forEach((n) => state.selected.add(n));
  } else if (state.selected.has(name)) {
    state.selected.delete(name);
  } else {
    state.selected.add(name);
  }
  state.anchor = name;
  render();
}

// ---------- desenho ----------

function paint(name) {
  const { card, size } = state.files.get(name);
  const warning = state.failed.get(name);
  const detail = card.querySelector(".detail");
  card.setAttribute("aria-pressed", String(state.selected.has(name)));
  detail.textContent = warning || size;
  detail.classList.toggle("error", Boolean(warning));
}

function renderTrail() {
  const steps = state.trail.map((handle, index) => {
    const last = index === state.trail.length - 1;
    return h("li", {}, last
      ? h("strong", { "aria-current": "location" }, handle.name)
      : h("button", {
        type: "button", class: "link", disabled: isBusy(),
        onclick: act(() => goTo(state.trail.slice(0, index + 1))),
      }, handle.name));
  });
  el.trail.replaceChildren(icon("folder"), ...steps);
  el.trail.hidden = steps.length === 0;
}

function render() {
  const busy = isBusy();
  const total = state.files.size;
  const chosen = state.selected.size;
  renderTrail();
  state.files.forEach((_, name) => paint(name));
  el.count.textContent = root()
    ? `${number(chosen)} de ${plural(
      total, "arquivo selecionado", "arquivos selecionados"
    )}`
    : "Escolha uma pasta para começar.";
  el.pick.disabled = busy;
  el.all.disabled = busy || total === 0;
  el.none.disabled = busy || chosen === 0;
  el.move.disabled = busy || chosen === 0;
  el.remove.disabled = busy || chosen === 0;
  el.move.classList.toggle("primary", chosen > 0);
  el.grid.classList.toggle("busy", busy);
}

function act(action) {
  return async () => {
    if (isBusy()) return;
    try {
      await action();
    } catch (error) {
      setStatus(el.status, describeError(error), true);
    }
    render();
  };
}

// ---------- operações ----------

async function pick() {
  const handle = await pickFolder("readwrite");
  if (handle) await goTo([handle]);
}

// Caminho completo só quando o destino está dentro da raiz aberta.
async function destinationPath(destination) {
  const inside = await root().resolve(destination);
  return inside
    ? [root().name, ...inside].join("/")
    : destination.name;
}

async function move() {
  const destination = await pickFolder("readwrite");
  if (!destination) return;
  setStatus(el.status, "");
  if (await destination.isSameEntry(current())) {
    setStatus(
      el.status,
      "O destino é a própria pasta de origem. Escolha outra pasta.", true
    );
    return;
  }
  await runBatch("move", destination, await destinationPath(destination));
}

async function runBatch(kind, destination, path) {
  const source = current();
  const folders = { sources: [source], destination };
  // Segue a ordem da grade, não a ordem dos cliques.
  const names = [...state.files.keys()].filter((n) => state.selected.has(n));
  const request = {
    kind,
    sources: [pathOf(state.trail)],
    destination: path,
    files: names.map((name) => ({ source: 0, name })),
  };
  const plan = await planBatch(request, folders);
  const confirmed = await confirmBatch(plan, async () => {
    await ensurePermission(source, "readwrite");
    if (destination) await ensurePermission(destination, "readwrite");
  });
  if (!confirmed) return;

  hideErrors(el.errors);
  setStatus(el.status, "");
  const bar = progressBar(el.progress, kind);
  try {
    const running = startBatch(request, folders, bar.update);
    render();
    const batch = await running;
    setStatus(el.status, batchResult(batch));
    showErrors(el.errors, batch);
    const failed = failedItems(batch).map((item) => item.name);
    state.selected = new Set(failed);
    state.failed = new Map(failed.map((n) => [n, VERBS[kind].notDone]));
  } catch (error) {
    setStatus(el.status, describeError(error), true);
  } finally {
    bar.remove();
  }
  await load();
}

// ---------- eventos ----------

export function initExplore() {
  el.pick.addEventListener("click", act(pick));
  el.all.addEventListener("click", act(() => {
    state.selected = new Set(state.files.keys());
  }));
  el.none.addEventListener("click", act(() => state.selected.clear()));
  el.move.addEventListener("click", act(move));
  el.remove.addEventListener("click", act(() => runBatch("delete", null, null)));
  document.addEventListener("batches-changed", render);
  if (!isSupported()) setStatus(el.status, UNSUPPORTED, true);
  render();
}

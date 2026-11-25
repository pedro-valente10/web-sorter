// Aba "Organizar por extensão" (SCRUM-56 e SCRUM-57).

import { api } from "./api.js";
import { isBusy, planBatch, startBatch } from "./batch-runner.js";
import { confirmBatch } from "./dialog.js";
import { hideErrors, showErrors } from "./error-panel.js";
import {
  describeError, droppedFolder, ensurePermission, isSupported, listEntries,
  pickFolder, UNSUPPORTED,
} from "./fs.js";
import { progressBar } from "./progress.js";
import {
  batchResult, fileCount, h, icon, joinNames, number, plural, setStatus,
  VERBS,
} from "./ui.js";

const MAX_LISTED = 200;
const $ = (id) => document.getElementById(id);

const el = {
  status: $("organize-status"),
  progress: $("organize-progress"),
  errors: $("organize-errors"),
  sources: $("source-list"),
  addSource: $("add-source"),
  addSourceLabel: $("add-source-label"),
  addSourceHint: $("add-source-hint"),
  warning: $("organize-warning"),
  count: $("extension-count"),
  clear: $("clear-extensions"),
  extensions: $("extension-list"),
  destination: $("destination-slot"),
  addDestination: $("add-destination"),
  changeDestination: $("change-destination"),
  summary: $("organize-summary"),
  summaryText: $("organize-summary-text"),
  run: $("run-organize"),
  hint: $("organize-hint"),
};

const state = {
  sources: [], // { handle, names }
  destination: null,
  files: [], // { source, name }, na mesma ordem enviada ao servidor
  groups: [],
  unchecked: new Set(),
  expanded: new Set(),
  sameFolder: false,
};

const label = (group) => group.extension || "sem extensão";
const mode = () => document.querySelector('[name="mode"]:checked').value;
const checkedGroups = () =>
  state.groups.filter((g) => !state.unchecked.has(g.extension));
const selectedFiles = () =>
  checkedGroups().flatMap((g) => g.indexes.map((i) => state.files[i]));

// ---------- estado ----------

async function reload() {
  for (const source of state.sources) {
    const { files } = await listEntries(source.handle);
    source.names = files.map((file) => file.name);
  }
  await summarize();
}

async function summarize() {
  const files = state.sources.flatMap((source, index) =>
    source.names.map((name) => ({ source: index, name })));
  const data = files.length === 0
    ? { extensions: [] }
    : await api("POST", "/extensions", { files: files.map((f) => f.name) });
  state.files = files;
  state.groups = data.extensions;
  await checkSameFolder();
}

async function checkSameFolder() {
  state.sameFolder = false;
  if (!state.destination) return;
  for (const { handle } of state.sources) {
    if (await handle.isSameEntry(state.destination)) state.sameFolder = true;
  }
}

async function addSource(handle) {
  for (const source of state.sources) {
    if (await source.handle.isSameEntry(handle)) {
      warn(`A pasta "${handle.name}" já está na lista de origem.`);
      return;
    }
  }
  const { files } = await listEntries(handle);
  state.sources.push({ handle, names: files.map((file) => file.name) });
  try {
    await summarize();
  } catch (error) {
    state.sources.pop();
    throw error;
  }
}

async function removeSource(source) {
  state.sources = state.sources.filter((s) => s !== source);
  await summarize();
}

async function setDestination(handle) {
  state.destination = handle;
  await checkSameFolder();
}

// ---------- desenho ----------

function warn(text) {
  el.warning.dataset.notice = text;
}

function folderCard(handle, detail, onRemove, disabled) {
  return h(
    "div", { class: "folder-card" },
    icon("folder"),
    h("div", {}, h("strong", {}, handle.name),
      detail ? h("span", { class: "muted" }, detail) : null),
    h("button", {
      type: "button", class: "icon-button", onclick: onRemove, disabled,
      "aria-label": `Remover a pasta ${handle.name}`,
    }, icon("close"))
  );
}

function extensionRow(group) {
  const open = state.expanded.has(group.extension);
  const checkbox = h("input", {
    type: "checkbox",
    checked: !state.unchecked.has(group.extension),
    disabled: isBusy(),
    onchange: (event) => {
      if (event.target.checked) state.unchecked.delete(group.extension);
      else state.unchecked.add(group.extension);
      render();
    },
  });
  const toggle = h("button", {
    type: "button", class: "icon-button toggle", "aria-expanded": String(open),
    "aria-label": `Ver os arquivos ${label(group)}`,
    onclick: () => {
      if (open) state.expanded.delete(group.extension);
      else state.expanded.add(group.extension);
      render();
    },
  }, icon("chevron"));
  return h(
    "li", {},
    h(
      "div", { class: "extension-row" },
      h("label", {}, checkbox, icon("file"), h(
        "span", {}, h("strong", {}, label(group)),
        h("span", { class: "muted" }, group.description)
      )),
      h("span", { class: "count" }, number(group.count)),
      toggle
    ),
    open ? fileList(group) : null
  );
}

function fileList(group) {
  const names = group.indexes.slice(0, MAX_LISTED)
    .map((i) => state.files[i].name);
  const rest = group.count - names.length;
  return h(
    "ul", { class: "extension-files" },
    ...names.map((name) => h("li", {}, name)),
    rest > 0 ? h("li", { class: "muted" }, `e mais ${number(rest)}`) : null
  );
}

function emptyExtensions() {
  const text = state.sources.length === 0
    ? "Escolha uma pasta de origem para ver as extensões"
    : "Nenhum arquivo nas pastas de origem.";
  return h("li", { class: "empty" }, icon("file"), h("span", {}, text));
}

function render() {
  const busy = isBusy();
  const checked = checkedGroups();
  const total = selectedFiles().length;
  const verb = VERBS[mode()].infinitive;

  el.sources.replaceChildren(...state.sources.map((source) => folderCard(
    source.handle, fileCount(source.names.length),
    act(() => removeSource(source)), busy
  )));
  const hasSources = state.sources.length > 0;
  el.addSource.classList.toggle("compact", hasSources);
  el.addSourceLabel.textContent =
    hasSources ? "Adicionar outra pasta" : "Arraste e solte uma pasta aqui";
  el.addSourceHint.hidden = hasSources;
  el.addSource.disabled = busy;

  el.count.textContent = state.groups.length === 0
    ? "Nenhuma extensão"
    : `${number(checked.length)} de ${plural(
      state.groups.length, "extensão selecionada", "extensões selecionadas"
    )}`;
  el.clear.hidden = state.groups.length === 0;
  el.clear.disabled = busy || checked.length === 0;
  el.extensions.replaceChildren(...(state.groups.length === 0
    ? [emptyExtensions()] : state.groups.map(extensionRow)));

  el.destination.replaceChildren(...(state.destination ? [folderCard(
    state.destination, null, act(() => setDestination(null)), busy
  )] : []));
  el.addDestination.hidden = Boolean(state.destination);
  el.addDestination.disabled = busy;
  el.changeDestination.hidden = !state.destination;
  el.changeDestination.disabled = busy;

  const warning = state.sameFolder
    ? "O destino é a própria pasta de origem. Escolha outra pasta."
    : el.warning.dataset.notice || "";
  setStatus(el.warning, warning, true);

  const ready = total > 0 && state.destination && !state.sameFolder;
  el.run.disabled = !ready || busy;
  el.run.textContent =
    total > 0 ? `${verb} ${fileCount(total)}` : `${verb} arquivos`;
  el.summary.hidden = !ready;
  if (ready) {
    const origins = joinNames(state.sources.map((s) => s.handle.name));
    el.summaryText.textContent =
      `${verb} ${fileCount(total)} de ` +
      `${plural(checked.length, "extensão", "extensões")} ` +
      `de ${origins} para ${state.destination.name}.`;
  }
  el.hint.hidden = Boolean(ready);
  for (const radio of document.querySelectorAll('[name="mode"]')) {
    radio.disabled = busy;
  }
}

// Executa uma ação da tela, mostra eventuais erros e redesenha.
function act(action) {
  return async (event) => {
    if (isBusy()) return;
    warn("");
    try {
      await action(event);
    } catch (error) {
      warn(describeError(error));
    }
    render();
  };
}

// ---------- execução ----------

async function run() {
  const kind = mode();
  const folders = {
    sources: state.sources.map((s) => s.handle),
    destination: state.destination,
  };
  const request = {
    kind,
    sources: folders.sources.map((handle) => handle.name),
    destination: state.destination.name,
    same_folder: state.sameFolder,
    files: selectedFiles(),
  };
  const plan = await planBatch(request, folders);
  const confirmed = await confirmBatch(plan, async () => {
    await ensurePermission(folders.destination, "readwrite");
    for (const source of folders.sources) {
      await ensurePermission(source, kind === "move" ? "readwrite" : "read");
    }
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
  } catch (error) {
    setStatus(el.status, describeError(error), true);
  } finally {
    bar.remove();
  }
  await reload();
}

// ---------- eventos ----------

function dropZone(node, onFolder) {
  node.addEventListener("dragover", (event) => {
    event.preventDefault();
    node.classList.add("dragging");
  });
  node.addEventListener("dragleave", () => node.classList.remove("dragging"));
  node.addEventListener("drop", (event) => {
    event.preventDefault();
    node.classList.remove("dragging");
    act(async () => onFolder(await droppedFolder(event)))(event);
  });
}

async function pickSource() {
  const handle = await pickFolder(mode() === "move" ? "readwrite" : "read");
  if (handle) await addSource(handle);
}

async function pickDestination() {
  const handle = await pickFolder("readwrite");
  if (handle) await setDestination(handle);
}

export function initOrganize() {
  el.addSource.addEventListener("click", act(pickSource));
  el.addDestination.addEventListener("click", act(pickDestination));
  el.changeDestination.addEventListener("click", act(pickDestination));
  dropZone(el.addSource, addSource);
  dropZone(el.addDestination, setDestination);
  el.clear.addEventListener("click", act(() => {
    state.groups.forEach((group) => state.unchecked.add(group.extension));
  }));
  for (const radio of document.querySelectorAll('[name="mode"]')) {
    radio.addEventListener("change", act(() => {}));
  }
  el.run.addEventListener("click", act(run));
  document.addEventListener("batches-changed", render);
  if (!isSupported()) warn(UNSUPPORTED);
  render();
}

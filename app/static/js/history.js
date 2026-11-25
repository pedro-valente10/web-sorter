// Histórico de operações, com retomada das que não terminaram.

import { api } from "./api.js";
import {
  isBusy, notifyBatchesChanged, resumeBatch, runningBatchIds,
} from "./batch-runner.js";
import { confirmDialog } from "./dialog.js";
import { hideErrors, showErrors } from "./error-panel.js";
import { describeError } from "./fs.js";
import { progressBar } from "./progress.js";
import { foldersToResume } from "./resume.js";
import {
  batchResult, button, dateTime, fileCount, folderName, folderTrail, h,
  joinNames, number, plural, setStatus, VERBS,
} from "./ui.js";

const PAGE = 200;
const $ = (id) => document.getElementById(id);

const el = {
  status: $("history-status"),
  progress: $("history-progress"),
  errors: $("history-errors"),
  list: $("history-list"),
  banner: $("resume-banner"),
};

const STATUS = {
  finished: "Concluído",
  interrupted: "Interrompido",
  open: "Não terminou",
  running: "Em andamento",
};

let refreshing = 0;

function title(batch) {
  const from = joinNames(batch.sources.map(folderName));
  const to = batch.destination ? ` para ${folderName(batch.destination)}` : "";
  return `${VERBS[batch.kind].infinitive} ` +
    `${fileCount(batch.progress.total)} de ${from}${to}`;
}

function resultText({ kind, progress }) {
  const parts = [VERBS[kind].done(progress.done)];
  if (progress.failed > 0) parts.push(`${number(progress.failed)} com erro`);
  if (progress.pending > 0) {
    parts.push(`${number(progress.pending)} sem resultado`);
  }
  return parts.join(" · ");
}

// ---------- detalhes ----------

const ITEM_STATUS = { done: "Concluído", pending: "Sem resultado" };

function itemRow(item) {
  const renamed = item.target_name && item.target_name !== item.name &&
    item.status === "done";
  return h(
    "li", { class: item.status },
    h("span", {}, renamed ? `${item.name} → ${item.target_name}` : item.name),
    h("span", {}, item.error || ITEM_STATUS[item.status])
  );
}

async function fillDetails(container, batchId) {
  const batch = await api("GET", `/batches/${batchId}`);
  const order = { failed: 0, pending: 1, done: 2 };
  const items = [...batch.items].sort(
    (a, b) => order[a.status] - order[b.status]
  );
  const list = h("ul", { class: "history-items" });
  const more = button("Mostrar mais", showMore, "link");
  function showMore() {
    list.append(...items.splice(0, PAGE).map(itemRow));
    more.hidden = items.length === 0;
  }
  showMore();
  container.replaceChildren(
    h("p", { class: "muted" },
      `De ${batch.sources.map(folderTrail).join(", ")}`,
      batch.destination ? ` para ${folderTrail(batch.destination)}` : ""),
    list, more
  );
}

// ---------- lista ----------

function resumeActions(batch) {
  return h(
    "div", { class: "row" },
    button("Retomar", () => resume(batch), "primary"),
    button("Descartar", () => discard(batch))
  );
}

function row(batch, running) {
  const status = batch.status === "open" && running ? "running" : batch.status;
  const body = h("div", { class: "history-body" });
  const details = h(
    "details", {
      ontoggle: () => {
        if (!details.open || body.hasChildNodes()) return;
        fillDetails(body, batch.id).catch((error) => {
          body.replaceChildren(h("p", { class: "error" }, error.message));
        });
      },
    },
    h(
      "summary", {},
      h("strong", {}, title(batch)),
      h("span", { class: `chip ${status}` }, STATUS[status]),
      h("span", { class: "muted" },
        `${dateTime(batch.created_at)} · ${resultText(batch)}`)
    ),
    body
  );
  return h("li", {}, details, status === "open" ? resumeActions(batch) : null);
}

function renderBanner(open) {
  el.banner.hidden = open.length === 0;
  el.banner.replaceChildren(...open.map((batch) => h(
    "div", { class: "row" },
    h("span", {}, h("strong", {}, "Esta operação não terminou: "),
      `${title(batch)} (${plural(
        batch.progress.pending, "arquivo restante", "arquivos restantes"
      )}).`),
    resumeActions(batch)
  )));
}

export async function refreshHistory() {
  refreshing += 1;
  const turn = refreshing;
  try {
    const [{ batches }, locks] = await Promise.all([
      api("GET", "/batches"), runningBatchIds(),
    ]);
    if (turn !== refreshing) return; // já há uma atualização mais nova
    const isRunning = (b) => locks.has(`web-sorter-batch-${b.id}`);
    el.list.replaceChildren(...(batches.length > 0
      ? batches.map((batch) => row(batch, isRunning(batch)))
      : [h("li", { class: "empty" }, "Nenhuma operação por enquanto.")]));
    renderBanner(batches.filter((b) => b.status === "open" && !isRunning(b)));
  } catch (error) {
    setStatus(el.status, describeError(error), true);
  }
}

// ---------- ações ----------

async function guarded(action) {
  if (isBusy()) {
    setStatus(el.status, "Espere a operação em andamento terminar.", true);
    return;
  }
  try {
    await action();
  } catch (error) {
    setStatus(el.status, describeError(error), true);
  }
}

function resume(batch) {
  window.location.hash = "historico";
  return guarded(async () => {
    const folders = await foldersToResume(batch);
    if (!folders) return;
    hideErrors(el.errors);
    setStatus(el.status, "");
    const bar = progressBar(el.progress, batch.kind);
    try {
      const finished = await resumeBatch(batch, folders, bar.update);
      setStatus(el.status, batchResult(finished));
      showErrors(el.errors, finished);
    } finally {
      bar.remove();
    }
  });
}

function discard(batch) {
  return guarded(async () => {
    const confirmed = await confirmDialog({
      title: "Descartar esta operação?",
      body: [h("p", { class: "muted" },
        "Nenhum arquivo é alterado: o que já foi feito continua como está " +
        "e o restante não será processado.")],
      confirmLabel: "Descartar",
      onConfirm: () => api("POST", `/batches/${batch.id}/discard`, {}),
    });
    if (confirmed) notifyBatchesChanged();
  });
}

export function initHistory() {
  document.addEventListener("batches-changed", refreshHistory);
  refreshHistory();
}

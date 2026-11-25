// Executa os lotes: mexe nos arquivos e registra cada resultado no servidor.

import { api } from "./api.js";
import {
  copyFile, describeError, entryNames, removeFile, removeIfEmpty, StepError,
} from "./fs.js";
import {
  clearReservation, forgetFolders, loadReservation, saveFolders,
  saveReservation,
} from "./handle-store.js";

let busy = false;

window.addEventListener("beforeunload", (event) => {
  if (busy) event.preventDefault();
});

export function isBusy() {
  return busy;
}

export function notifyBatchesChanged() {
  document.dispatchEvent(new Event("batches-changed"));
}

const lockName = (batch) => `web-sorter-batch-${batch.id}`;

// Lotes em execução nesta ou em outra aba do navegador.
export async function runningBatchIds() {
  const { held } = await navigator.locks.query();
  return new Set(held.map((lock) => lock.name));
}

export async function isRunning(batch) {
  return (await runningBatchIds()).has(lockName(batch));
}

async function exclusively(action) {
  if (busy) throw new Error("Já existe uma operação em andamento.");
  busy = true;
  try {
    return await action();
  } finally {
    busy = false;
    notifyBatchesChanged();
  }
}

async function processItem(batch, item, { sources, destination }) {
  const source = sources[item.source];
  if (batch.kind !== "delete") {
    await copyFile(
      source, item.name, destination, item.target_name,
      () => saveReservation(batch, item.target_name)
    ).finally(() => clearReservation(batch));
  }
  if (batch.kind !== "copy") await removeFile(source, item.name);
}

async function recordResult(batch, item, failure) {
  const url = `/batches/${batch.id}/items/${item.position}/result`;
  try {
    await api("POST", url, failure);
  } catch (error) {
    // O registro pode ter chegado mesmo sem resposta; confere antes de parar.
    const current = await api("GET", `/batches/${batch.id}`);
    const saved = current.items.find((i) => i.position === item.position);
    if (saved.status === "pending") await api("POST", url, failure);
  }
}

async function processAll(batch, folders, onProgress) {
  const total = batch.items.length;
  for (const [index, item] of batch.items.entries()) {
    onProgress(index + 1, total);
    let failure = {};
    try {
      await processItem(batch, item, folders);
    } catch (error) {
      if (!(error instanceof StepError)) throw error;
      failure = { step: error.step, code: error.code };
    }
    await recordResult(batch, item, failure);
  }
  const finished = await api("POST", `/batches/${batch.id}/finish`, {});
  await forgetFolders(batch);
  return finished;
}

async function runLocked(batch, prepare, folders, onProgress) {
  return navigator.locks.request(
    lockName(batch), { ifAvailable: true }, async (lock) => {
      if (!lock) {
        throw new Error("Este lote já está em execução em outra aba.");
      }
      try {
        return await processAll(await prepare(), folders, onProgress);
      } catch (error) {
        throw new Error(
          `${describeError(error)} A operação parou; retome pelo histórico.`
        );
      }
    }
  );
}

async function takenNames({ destination }) {
  return destination ? entryNames(destination) : [];
}

export async function planBatch(request, folders) {
  return api("POST", "/batches/plan", {
    ...request, taken_names: await takenNames(folders),
  });
}

export function startBatch(request, folders, onProgress) {
  return exclusively(async () => {
    const batch = await api("POST", "/batches", {
      ...request, taken_names: await takenNames(folders),
    });
    await saveFolders(batch, folders);
    return runLocked(batch, async () => batch, folders, onProgress);
  });
}

export function resumeBatch(batch, folders, onProgress) {
  return exclusively(async () => {
    await saveFolders(batch, folders);
    const prepare = async () => {
      const leftover = await loadReservation(batch);
      if (leftover) await removeIfEmpty(folders.destination, leftover);
      return api("POST", `/batches/${batch.id}/resume`, {
        taken_names: await takenNames(folders),
      });
    };
    return runLocked(batch, prepare, folders, onProgress);
  });
}

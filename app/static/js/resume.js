// Recupera as pastas de um lote interrompido, para retomá-lo.

import { confirmDialog } from "./dialog.js";
import { describeError, ensurePermission, pickFolder } from "./fs.js";
import { loadFolders } from "./handle-store.js";
import { button, folderName, h } from "./ui.js";

function permissionsFor(batch) {
  return batch.kind === "copy" ? "read" : "readwrite";
}

async function authorize(batch, { sources, destination }) {
  if (destination) await ensurePermission(destination, "readwrite");
  for (const source of sources) {
    await ensurePermission(source, permissionsFor(batch));
  }
}

// Uma linha por pasta que precisa ser escolhida de novo.
function folderSlot(path, role, mode, onPick) {
  const name = folderName(path);
  const status = h("span", { class: "muted" }, "não escolhida");
  const choose = button("Escolher", async () => {
    try {
      const handle = await pickFolder(mode);
      if (!handle) return;
      if (handle.name !== name) {
        status.textContent = `Escolha a pasta "${name}", não "${handle.name}".`;
        status.className = "error";
        return;
      }
      status.textContent = "escolhida";
      status.className = "ok";
      onPick(handle);
    } catch (error) {
      status.textContent = describeError(error);
      status.className = "error";
    }
  });
  return h(
    "li", {}, h("span", {}, `${role}: `, h("strong", {}, name)), status, choose
  );
}

async function askFolders(batch) {
  const folders = { sources: batch.sources.map(() => null), destination: null };
  const slots = batch.sources.map((path, index) => folderSlot(
    path, "Origem", permissionsFor(batch),
    (handle) => { folders.sources[index] = handle; }
  ));
  if (batch.destination) {
    slots.push(folderSlot(
      batch.destination, "Destino", "readwrite",
      (handle) => { folders.destination = handle; }
    ));
  }
  const confirmed = await confirmDialog({
    title: "Escolha as mesmas pastas para retomar",
    body: [
      h("p", { class: "muted" },
        "Este navegador não guardou as pastas desta operação."),
      h("ul", { class: "folder-slots" }, ...slots),
    ],
    confirmLabel: "Retomar",
    onConfirm: async () => {
      const missing = folders.sources.includes(null) ||
        (batch.destination && !folders.destination);
      if (missing) throw new Error("Escolha todas as pastas.");
      for (const source of folders.sources) {
        if (folders.destination &&
            await source.isSameEntry(folders.destination)) {
          throw new Error("O destino é a própria pasta de origem.");
        }
      }
      await authorize(batch, folders);
    },
  });
  return confirmed ? folders : null;
}

// Devolve as pastas autorizadas ou null se o usuário desistir.
export async function foldersToResume(batch) {
  const saved = await loadFolders(batch);
  if (!saved) return askFolders(batch);
  await authorize(batch, saved);
  return saved;
}

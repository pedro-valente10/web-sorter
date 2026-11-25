// Acesso às pastas do usuário (File System Access API).

export const UNSUPPORTED =
  "Seu navegador não permite acessar pastas. Use o Chrome ou o Edge.";

export function isSupported() {
  return "showDirectoryPicker" in window;
}

// Devolve a pasta escolhida ou null se o usuário cancelar.
export async function pickFolder(mode) {
  if (!isSupported()) throw new Error(UNSUPPORTED);
  try {
    return await window.showDirectoryPicker({ mode });
  } catch (error) {
    if (error.name === "AbortError") return null;
    throw error;
  }
}

export async function droppedFolder(event) {
  const [item] = event.dataTransfer.items;
  if (!item || !item.getAsFileSystemHandle) throw new Error(UNSUPPORTED);
  const handle = await item.getAsFileSystemHandle();
  if (!handle || handle.kind !== "directory") {
    throw new Error("Solte uma pasta, não um arquivo.");
  }
  return handle;
}

const MESSAGES = {
  NotFoundError: "A pasta não foi encontrada. Ela pode ter sido movida, " +
    "renomeada ou apagada.",
  NotAllowedError: "O acesso à pasta não foi autorizado.",
  SecurityError: "O navegador bloqueou o acesso a esta pasta.",
};

// Os erros do navegador vêm em inglês; os da aplicação já são claros.
export function describeError(error) {
  if (!(error instanceof DOMException)) return error.message;
  return MESSAGES[error.name] || "Não foi possível acessar a pasta.";
}

// Precisa ser chamada a partir de um clique do usuário.
export async function ensurePermission(handle, mode) {
  if (!handle.queryPermission) return;
  if (await handle.queryPermission({ mode }) === "granted") return;
  let answer = "denied";
  try {
    answer = await handle.requestPermission({ mode });
  } catch (error) {
    throw new Error(`Clique de novo para autorizar a pasta "${handle.name}".`);
  }
  if (answer !== "granted") {
    throw new Error(`O acesso à pasta "${handle.name}" não foi autorizado.`);
  }
}

const natural = new Intl.Collator("pt-BR", {
  numeric: true, sensitivity: "base",
});

export async function listEntries(directory) {
  const files = [];
  const folders = [];
  for await (const [name, handle] of directory.entries()) {
    (handle.kind === "file" ? files : folders).push({ name, handle });
  }
  const byName = (a, b) => natural.compare(a.name, b.name);
  return { files: files.sort(byName), folders: folders.sort(byName) };
}

export async function entryNames(directory) {
  const names = [];
  for await (const name of directory.keys()) names.push(name);
  return names;
}

export class StepError extends Error {
  constructor(step, code) {
    super(code);
    this.step = step;
    this.code = code;
  }
}

async function step(name, action) {
  try {
    return await action();
  } catch (error) {
    if (error instanceof StepError) throw error;
    throw new StepError(name, error.name || "Error");
  }
}

async function exists(directory, name) {
  try {
    await directory.getFileHandle(name);
    return true;
  } catch (error) {
    if (error.name === "NotFoundError") return false;
    throw error;
  }
}

// Copia em streaming e nunca sobrescreve um arquivo existente.
// onReserve é chamado quando o nome está livre, antes de criar o arquivo.
export async function copyFile(source, name, target, targetName, onReserve) {
  const file = await step("read", async () =>
    (await source.getFileHandle(name)).getFile());

  const output = await step("write", async () => {
    if (await exists(target, targetName)) {
      throw new StepError("write", "TargetExists");
    }
    if (onReserve) await onReserve();
    return target.getFileHandle(targetName, { create: true });
  });

  try {
    await step("write", async () => {
      const writable = await output.createWritable();
      try {
        await file.stream().pipeTo(writable);
      } catch (error) {
        // Arquivo bloqueado por outro programa: o fluxo falha com TypeError.
        if (error instanceof TypeError) {
          throw new StepError("read", "NotReadableError");
        }
        const reading = ["NotReadableError", "NotFoundError"];
        const failed = reading.includes(error.name) ? "read" : "write";
        throw new StepError(failed, error.name);
      }
      if ((await output.getFile()).size !== file.size) {
        throw new StepError("write", "SizeMismatch");
      }
    });
  } catch (error) {
    // Apaga apenas o arquivo incompleto que acabou de ser criado aqui.
    await target.removeEntry(targetName).catch(() => {});
    throw error;
  }
}

// Remove o arquivo vazio que uma cópia interrompida deixou no destino.
export async function removeIfEmpty(directory, name) {
  try {
    const file = await (await directory.getFileHandle(name)).getFile();
    if (file.size === 0) await directory.removeEntry(name);
  } catch (error) {
    if (error.name !== "NotFoundError") throw error;
  }
}

export async function removeFile(directory, name) {
  await step("remove", () => directory.removeEntry(name));
}

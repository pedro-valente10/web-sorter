// Guarda no navegador (IndexedDB) as pastas dos lotes em andamento, para
// que possam ser retomados depois de fechar a página.

const DATABASE = "web-sorter";
const STORE = "batch-folders";

function open() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function run(mode, action) {
  const database = await open();
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE, mode);
      const request = action(transaction.objectStore(STORE));
      transaction.oncomplete = () => resolve(request.result);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

// Falhar aqui não pode impedir o lote: sem a referência, o usuário apenas
// terá de escolher as pastas de novo ao retomar.
export async function saveFolders(batch, folders) {
  const record = { ...folders, createdAt: batch.created_at };
  await run("readwrite", (s) => s.put(record, batch.id)).catch(() => {});
}

export async function loadFolders(batch) {
  const record = await run("readonly", (s) => s.get(batch.id))
    .catch(() => null);
  // A data evita usar a pasta de um lote antigo com o mesmo número.
  return record && record.createdAt === batch.created_at ? record : null;
}

export async function forgetFolders(batch) {
  await run("readwrite", (s) => s.delete(batch.id)).catch(() => {});
  await clearReservation(batch);
}

// Nome que este lote está criando agora no destino. Se a página fechar no
// meio da cópia, é o único arquivo incompleto que pode ter sobrado.
const reservationKey = (batch) => `writing-${batch.id}`;

export async function saveReservation(batch, name) {
  const record = { name, createdAt: batch.created_at };
  await run("readwrite", (s) => s.put(record, reservationKey(batch)))
    .catch(() => {});
}

export async function loadReservation(batch) {
  const record = await run("readonly", (s) => s.get(reservationKey(batch)))
    .catch(() => null);
  return record && record.createdAt === batch.created_at ? record.name : null;
}

export async function clearReservation(batch) {
  await run("readwrite", (s) => s.delete(reservationKey(batch)))
    .catch(() => {});
}

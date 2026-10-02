const $ = (s) => document.querySelector(s);
const grid = $('#grid'), statusEl = $('#status'), countEl = $('#count');
const btns = { all: $('#all'), none: $('#none'), move: $('#move'), del: $('#del') };

const IMG = /\.(jpe?g|png|gif|webp|bmp|avif)$/i;
const VID = /\.(mp4|webm|mov|m4v|ogv)$/i;
const THUMB_WIDTH = 200;   // preview de baixa resolução
const CONCURRENCY = 4;     // quantos previews carregam em paralelo

let srcDir = null;
let items = new Map();     // id -> { id, name, handle, url }
let selected = new Set();  // ids
let lastClicked = null;

if (!window.showDirectoryPicker) {
  statusEl.textContent = 'Seu navegador não suporta acesso a pastas. Use Chrome, Edge ou outro navegador baseado em Chromium.';
  $('#open').disabled = true;
}

/* ---------- Carregar pasta ---------- */
$('#open').onclick = async () => {
  try {
    srcDir = await showDirectoryPicker({ mode: 'readwrite' });
  } catch { return; } // usuário cancelou
  await loadFolder();
};

async function loadFolder() {
  items.forEach((it) => it.url && URL.revokeObjectURL(it.url));
  items.clear(); selected.clear(); lastClicked = null;
  grid.replaceChildren();
  setStatus('Lendo pasta…');

  const list = [];
  for await (const [name, handle] of srcDir.entries()) {
    if (handle.kind === 'file') list.push({ name, handle });
  }
  list.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));

  const frag = document.createDocumentFragment();
  list.forEach((f, i) => {
    const it = { id: String(i), ...f, url: null };
    items.set(it.id, it);
    const card = document.createElement('div');
    card.className = 'card';
    card.dataset.id = it.id;
    card.innerHTML = '<div class="thumb"></div><div class="name"></div>';
    card.querySelector('.name').textContent = f.name;
    card.title = f.name;
    frag.appendChild(card);
    observer.observe(card);
  });
  grid.appendChild(frag);
  setStatus(list.length ? `${srcDir.name} — ${list.length} arquivo(s). Clique para selecionar (Shift para intervalo).` : 'Pasta vazia.');
  updateUI();
}

/* ---------- Previews (lazy + fila limitada) ---------- */
const queue = [];
let running = 0;

const observer = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    observer.unobserve(e.target);
    queue.push(e.target);
  }
  pump();
}, { rootMargin: '300px' });

function pump() {
  while (running < CONCURRENCY && queue.length) {
    const card = queue.shift();
    running++;
    makePreview(card).finally(() => { running--; pump(); });
  }
}

async function makePreview(card) {
  const it = items.get(card.dataset.id);
  if (!it) return;
  const thumb = card.querySelector('.thumb');
  try {
    const file = await it.handle.getFile();
    if (IMG.test(it.name)) {
      const bmp = await createImageBitmap(file, { resizeWidth: THUMB_WIDTH, resizeQuality: 'low' });
      const canvas = document.createElement('canvas');
      canvas.width = bmp.width; canvas.height = bmp.height;
      canvas.getContext('2d').drawImage(bmp, 0, 0);
      bmp.close();
      thumb.replaceChildren(canvas);
    } else if (VID.test(it.name)) {
      it.url = URL.createObjectURL(file);
      const v = document.createElement('video');
      v.muted = true; v.preload = 'metadata'; v.src = it.url + '#t=0.5';
      thumb.replaceChildren(v);
    } else {
      thumb.textContent = (it.name.split('.').pop() || 'arquivo').toUpperCase().slice(0, 5);
    }
  } catch {
    thumb.textContent = 'sem preview';
  }
}

/* ---------- Seleção ---------- */
grid.addEventListener('click', (e) => {
  const card = e.target.closest('.card');
  if (!card) return;
  const id = card.dataset.id;

  if (e.shiftKey && lastClicked !== null) {
    const cards = [...grid.children];
    const a = cards.findIndex((c) => c.dataset.id === lastClicked);
    const b = cards.indexOf(card);
    const [from, to] = a < b ? [a, b] : [b, a];
    for (let i = from; i <= to; i++) setSelected(cards[i], true);
  } else {
    setSelected(card, !selected.has(id));
  }
  lastClicked = id;
  updateUI();
});

function setSelected(card, on) {
  const id = card.dataset.id;
  on ? selected.add(id) : selected.delete(id);
  card.classList.toggle('selected', on);
}

btns.all.onclick = () => { grid.childNodes.forEach((c) => setSelected(c, true)); updateUI(); };
btns.none.onclick = () => { grid.childNodes.forEach((c) => setSelected(c, false)); updateUI(); };

/* ---------- Deletar ---------- */
btns.del.onclick = async () => {
  const n = selected.size;
  if (!n || !confirm(`Deletar ${n} arquivo(s) permanentemente? Isso não vai para a lixeira.`)) return;
  await runBatch('Deletando', async (it) => {
    await srcDir.removeEntry(it.name);
  });
};

/* ---------- Mover (copia para o destino e remove da origem) ---------- */
btns.move.onclick = async () => {
  if (!selected.size) return;
  let dest;
  try {
    dest = await showDirectoryPicker({ mode: 'readwrite' });
  } catch { return; }
  if (await dest.isSameEntry(srcDir)) { alert('O destino é a própria pasta de origem.'); return; }

  await runBatch('Movendo', async (it) => {
    const file = await it.handle.getFile();
    const name = await uniqueName(dest, it.name);
    const out = await (await dest.getFileHandle(name, { create: true })).createWritable();
    await file.stream().pipeTo(out);       // cópia em streaming (não carrega tudo na memória)
    await srcDir.removeEntry(it.name);     // só remove depois de copiar com sucesso
  });
};

async function uniqueName(dir, name) {
  const dot = name.lastIndexOf('.');
  const base = dot > 0 ? name.slice(0, dot) : name;
  const ext = dot > 0 ? name.slice(dot) : '';
  let candidate = name, n = 1;
  while (true) {
    try { await dir.getFileHandle(candidate); } catch { return candidate; }
    candidate = `${base} (${n++})${ext}`;
  }
}

/* ---------- Execução em lote ---------- */
async function runBatch(label, fn) {
  const ids = [...selected];
  let done = 0, failed = 0;
  setButtons(false);
  for (const id of ids) {
    const it = items.get(id);
    setStatus(`${label}… ${done + failed + 1}/${ids.length}`);
    try {
      await fn(it);
      if (it.url) URL.revokeObjectURL(it.url);
      grid.querySelector(`.card[data-id="${id}"]`)?.remove();
      items.delete(id); selected.delete(id);
      done++;
    } catch (err) {
      console.error(it.name, err);
      failed++;
    }
  }
  setStatus(`${done} arquivo(s) processado(s)${failed ? `, ${failed} com erro (veja o console)` : ''}. Restam ${items.size}.`);
  updateUI();
}

/* ---------- UI ---------- */
function setStatus(t) { statusEl.textContent = t; }
function setButtons(on) {
  btns.all.disabled = !on || !items.size;
  btns.none.disabled = !on || !selected.size;
  btns.move.disabled = !on || !selected.size;
  btns.del.disabled = !on || !selected.size;
}
function updateUI() {
  countEl.textContent = items.size ? `${selected.size} selecionado(s) de ${items.size}` : '';
  setButtons(true);
}
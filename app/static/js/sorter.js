(() => {
  "use strict";

  const THUMBNAIL_WIDTH = 240;
  const IMAGE_EXTENSIONS = new Set(
    ["jpg", "jpeg", "png", "gif", "webp", "bmp", "avif"]
  );
  const VIDEO_EXTENSIONS = new Set(["mp4", "webm", "mov", "m4v", "ogv"]);

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]').content;
  const el = {
    pick: document.getElementById("pick-folder"),
    status: document.getElementById("status"),
    recent: document.getElementById("recent"),
    recentList: document.getElementById("recent-list"),
    panel: document.getElementById("session-panel"),
    destinationForm: document.getElementById("destination-form"),
    destinationName: document.getElementById("destination-name"),
    filter: document.getElementById("filter"),
    apply: document.getElementById("apply"),
    progress: document.getElementById("progress"),
    grid: document.getElementById("grid"),
  };

  const state = {
    dirHandle: null,
    session: null,
    decisions: new Map(), // caminho -> decisão vinda do servidor
    cards: new Map(), // nome do arquivo -> card
  };

  // ---------- utilidades ----------

  function setStatus(text, isError = false) {
    el.status.textContent = text;
    el.status.className = isError ? "error" : "muted";
  }

  async function api(method, url, body) {
    const options = { method, headers: { "X-CSRF-Token": csrfToken } };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    if (response.status === 401) {
      window.location.href = "/login";
      throw new Error("Sessão expirada.");
    }
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Erro inesperado.");
    }
    return data;
  }

  function extensionOf(name) {
    const dot = name.lastIndexOf(".");
    return dot > 0 ? name.slice(dot + 1).toLowerCase() : "";
  }

  function makeButton(label, className = "") {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    if (className) button.className = className;
    return button;
  }

  // Decisões já aplicadas (arquivo movido/excluído) não valem para um
  // arquivo de mesmo nome que apareça de novo na pasta.
  function activeDecision(name) {
    const decision = state.decisions.get(name);
    if (!decision) return null;
    if (decision.applied && decision.action !== "keep") return null;
    return decision;
  }

  // ---------- pré-visualização (carregada sob demanda) ----------

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      observer.unobserve(entry.target);
      const card = state.cards.get(entry.target.dataset.name);
      if (card) loadPreview(card);
    }
  }, { rootMargin: "300px" });

  async function loadPreview(card) {
    const extension = extensionOf(card.name);
    try {
      if (IMAGE_EXTENSIONS.has(extension)) {
        const file = await card.handle.getFile();
        const bitmap = await createImageBitmap(file, {
          resizeWidth: THUMBNAIL_WIDTH,
          resizeQuality: "low",
        });
        const canvas = document.createElement("canvas");
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        canvas.getContext("2d").drawImage(bitmap, 0, 0);
        bitmap.close();
        card.preview.replaceChildren(canvas);
      } else if (VIDEO_EXTENSIONS.has(extension)) {
        const file = await card.handle.getFile();
        const video = document.createElement("video");
        card.objectUrl = URL.createObjectURL(file);
        video.muted = true;
        video.preload = "metadata";
        video.src = `${card.objectUrl}#t=0.1`;
        card.preview.replaceChildren(video);
      }
    } catch (error) {
      // Sem pré-visualização: o card mantém o rótulo da extensão.
    }
  }

  // ---------- cards ----------

  function buildCard(name, handle) {
    const root = document.createElement("article");
    root.className = "card";
    root.dataset.name = name;

    const preview = document.createElement("div");
    preview.className = "preview";
    preview.textContent = extensionOf(name).toUpperCase() || "ARQ";

    const label = document.createElement("p");
    label.className = "name";
    label.textContent = name;
    label.title = name;

    const badge = document.createElement("p");
    badge.className = "badge";

    const select = document.createElement("select");
    select.setAttribute("aria-label", `Mover ${name} para`);
    const removeButton = makeButton("Excluir", "danger");
    const keepButton = makeButton("Manter");
    const undoButton = makeButton("Desfazer");

    const actions = document.createElement("div");
    actions.className = "actions";
    actions.append(select, removeButton, keepButton, undoButton);
    root.append(preview, label, badge, actions);

    select.addEventListener("change", () => {
      if (select.value) decide(name, "move", select.value);
    });
    removeButton.addEventListener("click", () => decide(name, "delete"));
    keepButton.addEventListener("click", () => decide(name, "keep"));
    undoButton.addEventListener("click", () => undoDecision(name));

    return {
      name, handle, root, preview, badge, select, undoButton,
      objectUrl: null,
    };
  }

  function matchesFilter(decision) {
    const filter = el.filter.value;
    if (filter === "all") return true;
    if (filter === "pending") return !decision;
    return Boolean(decision) && decision.action === filter;
  }

  function renderCard(card) {
    const decision = activeDecision(card.name);
    card.root.dataset.state = decision ? decision.action : "pending";
    card.select.value =
      decision && decision.action === "move" ? decision.destination : "";
    card.undoButton.hidden = !decision || decision.applied;
    card.badge.textContent = describe(decision);
    card.root.hidden = !matchesFilter(decision);
  }

  function describe(decision) {
    if (!decision) return "";
    const labels = {
      move: `Mover → ${decision.destination}`,
      delete: "Excluir",
      keep: "Manter",
    };
    return labels[decision.action] + (decision.applied ? " (aplicado)" : "");
  }

  function renderDestinations() {
    for (const card of state.cards.values()) {
      const placeholder = new Option("Mover para…", "");
      const options = state.session.destinations.map(
        (name) => new Option(name, name)
      );
      card.select.replaceChildren(placeholder, ...options);
      renderCard(card);
    }
  }

  function renderAll() {
    for (const card of state.cards.values()) renderCard(card);
  }

  function clearGrid() {
    for (const card of state.cards.values()) {
      observer.unobserve(card.root);
      if (card.objectUrl) URL.revokeObjectURL(card.objectUrl);
    }
    state.cards.clear();
    el.grid.replaceChildren();
  }

  function removeCard(name) {
    const card = state.cards.get(name);
    if (!card) return;
    observer.unobserve(card.root);
    if (card.objectUrl) URL.revokeObjectURL(card.objectUrl);
    card.root.remove();
    state.cards.delete(name);
  }

  // ---------- pasta e sessão ----------

  async function scanFolder() {
    clearGrid();
    const entries = [];
    for await (const [name, handle] of state.dirHandle.entries()) {
      if (handle.kind === "file") entries.push({ name, handle });
    }
    entries.sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { numeric: true })
    );
    const fragment = document.createDocumentFragment();
    for (const { name, handle } of entries) {
      const card = buildCard(name, handle);
      state.cards.set(name, card);
      fragment.append(card.root);
    }
    el.grid.append(fragment);
    for (const card of state.cards.values()) observer.observe(card.root);
  }

  async function pickFolder() {
    if (!("showDirectoryPicker" in window)) {
      setStatus("Use o Chrome, Edge ou outro navegador Chromium.", true);
      return;
    }
    let handle;
    try {
      handle = await window.showDirectoryPicker({ mode: "readwrite" });
    } catch (error) {
      if (error.name !== "AbortError") setStatus(error.message, true);
      return;
    }
    setStatus("Carregando…");
    try {
      const data = await api("POST", "/api/sessions", {
        folder_name: handle.name,
      });
      state.dirHandle = handle;
      state.session = data.session;
      state.decisions = new Map(data.decisions.map((d) => [d.path, d]));
      await scanFolder();
      el.panel.hidden = false;
      renderDestinations();
      await refreshSummary();
      await loadRecentSessions();
      reportResume(data.decisions);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function reportResume(decisions) {
    const missing = decisions.filter(
      (d) => !d.applied && !state.cards.has(d.path)
    ).length;
    let message = `Pasta "${state.session.folder_name}": ` +
      `${state.cards.size} arquivo(s).`;
    if (decisions.length > 0) message += " Decisões anteriores restauradas.";
    if (missing > 0) {
      message += ` ${missing} decisão(ões) de arquivos que não estão mais aqui.`;
    }
    setStatus(message);
  }

  async function loadRecentSessions() {
    try {
      const data = await api("GET", "/api/sessions");
      el.recentList.replaceChildren(...data.sessions.map((session) => {
        const item = document.createElement("li");
        const when = new Date(session.updated_at).toLocaleString("pt-BR");
        item.textContent = `${session.folder_name} — ${when}`;
        return item;
      }));
      el.recent.hidden = data.sessions.length === 0;
    } catch (error) {
      el.recent.hidden = true;
    }
  }

  // ---------- decisões ----------

  async function decide(name, action, destination) {
    const card = state.cards.get(name);
    try {
      const body = { path: name, action };
      if (destination) body.destination = destination;
      const decision = await api(
        "PUT", `/api/sessions/${state.session.id}/decisions`, body
      );
      state.decisions.set(name, decision);
      await refreshSummary();
    } catch (error) {
      setStatus(error.message, true);
    }
    if (card) renderCard(card);
  }

  async function undoDecision(name) {
    try {
      await api("DELETE", `/api/sessions/${state.session.id}/decisions`, {
        path: name,
      });
      state.decisions.delete(name);
      await refreshSummary();
    } catch (error) {
      setStatus(error.message, true);
    }
    const card = state.cards.get(name);
    if (card) renderCard(card);
  }

  async function addDestination(event) {
    event.preventDefault();
    try {
      const response = await api(
        "POST",
        `/api/sessions/${state.session.id}/destinations`,
        { name: el.destinationName.value }
      );
      state.session = response;
      el.destinationName.value = "";
      renderDestinations();
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function refreshSummary() {
    const summary = await api(
      "GET", `/api/sessions/${state.session.id}/summary`
    );
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

  async function fileExists(directory, name) {
    try {
      await directory.getFileHandle(name);
      return true;
    } catch (error) {
      if (error.name === "NotFoundError") return false;
      throw error;
    }
  }

  async function applyOne(decision) {
    if (decision.action === "keep") return;
    const card = state.cards.get(decision.path);
    if (decision.action === "delete") {
      await state.dirHandle.removeEntry(decision.path);
      return;
    }
    const target = await state.dirHandle.getDirectoryHandle(
      decision.destination, { create: true }
    );
    if (await fileExists(target, decision.path)) {
      throw new Error("já existe um arquivo com esse nome no destino");
    }
    const source = await card.handle.getFile();
    const output = await (
      await target.getFileHandle(decision.path, { create: true })
    ).createWritable();
    await source.stream().pipeTo(output);
    await state.dirHandle.removeEntry(decision.path);
  }

  async function applyDecisions() {
    const todo = [...state.decisions.values()].filter(
      (d) => !d.applied && state.cards.has(d.path)
    );
    if (todo.length === 0) {
      setStatus("Não há decisões para aplicar.");
      return;
    }
    const deletions = todo.filter((d) => d.action === "delete").length;
    const confirmed = window.confirm(
      `Aplicar ${todo.length} decisão(ões) nesta pasta?\n` +
      `${deletions} arquivo(s) serão excluídos definitivamente.`
    );
    if (!confirmed) return;

    let done = 0;
    const failures = [];
    for (const decision of todo) {
      try {
        await applyOne(decision);
        const applied = await api(
          "POST",
          `/api/sessions/${state.session.id}/decisions/applied`,
          { path: decision.path }
        );
        state.decisions.set(decision.path, applied);
        if (decision.action !== "keep") removeCard(decision.path);
        done += 1;
      } catch (error) {
        failures.push(`${decision.path}: ${error.message}`);
      }
    }
    await refreshSummary();
    if (failures.length > 0) {
      setStatus(
        `${done} aplicada(s); ${failures.length} falhou(aram): ` +
        failures.slice(0, 3).join("; "),
        true
      );
    } else {
      setStatus(`${done} decisão(ões) aplicada(s).`);
    }
  }

  // ---------- eventos ----------

  el.pick.addEventListener("click", pickFolder);
  el.destinationForm.addEventListener("submit", addDestination);
  el.filter.addEventListener("change", renderAll);
  el.apply.addEventListener("click", applyDecisions);
  loadRecentSessions();
})();

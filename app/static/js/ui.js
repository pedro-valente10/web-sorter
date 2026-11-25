// Utilidades de interface: criação de elementos, ícones e textos.

const SVG = "http://www.w3.org/2000/svg";

const ICONS = {
  folder: "M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2.5h9A1.5 1.5 0 0 1 21 9v8.5" +
    "a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z",
  file: "M6 3h8l4 4v14H6zM14 3v4h4",
  image: "M4 5h16v14H4zM4 16l4.5-4.5 4 4 2.5-2.5 5 5M15.5 9.5h.01",
  close: "M6 6l12 12M18 6L6 18",
  plus: "M12 4v16M4 12h16",
  chevron: "M9 5l7 7-7 7",
  check: "M5 12.5l4.5 4.5L19 7.5",
  warning: "M12 4l9 16H3zM12 10v4M12 17h.01",
  arrow: "M4 12h16M14 6l6 6-6 6",
};

export function icon(name) {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", `icon icon-${name}`);
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS(SVG, "path");
  path.setAttribute("d", ICONS[name]);
  svg.append(path);
  return svg;
}

// h("button", { class: "x", onclick: fn }, "texto", outroElemento)
export function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "class") node.className = value;
    else if (key in node && key !== "list") node[key] = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  node.append(...children.filter((c) => c !== null && c !== undefined));
  return node;
}

export function button(label, onclick, className = "") {
  return h("button", { type: "button", class: className, onclick }, label);
}

export function number(value) {
  return value.toLocaleString("pt-BR", { useGrouping: "always" });
}

export function plural(count, one, many) {
  return `${number(count)} ${count === 1 ? one : many}`;
}

export function fileCount(count) {
  return plural(count, "arquivo", "arquivos");
}

export function bytes(size) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = size;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const digits = unit === 0 ? 0 : 1;
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  }) + ` ${units[unit]}`;
}

export function dateTime(iso) {
  return new Date(iso).toLocaleString("pt-BR", {
    dateStyle: "short", timeStyle: "short",
  });
}

// "Fotos/2025/Viagem" -> "Viagem" e "Fotos › 2025 › Viagem"
export function folderName(path) {
  return path.slice(path.lastIndexOf("/") + 1);
}

export function folderTrail(path) {
  return path.split("/").join(" › ");
}

export function joinNames(names) {
  if (names.length < 2) return names.join("");
  return `${names.slice(0, -1).join(", ")} e ${names.at(-1)}`;
}

export function setStatus(node, text, isError = false) {
  node.textContent = text;
  node.classList.toggle("error", isError);
  node.hidden = !text;
}

export const VERBS = {
  copy: {
    infinitive: "Copiar", gerund: "Copiando",
    done: (n) => plural(n, "copiado", "copiados"),
    notDone: "Não copiado",
    notDoneMany: (n) =>
      `${fileCount(n)} ${n === 1 ? "não foi copiado" : "não foram copiados"}`,
  },
  move: {
    infinitive: "Mover", gerund: "Movendo",
    done: (n) => plural(n, "movido", "movidos"),
    notDone: "Não movido",
    notDoneMany: (n) =>
      `${fileCount(n)} ${n === 1 ? "não foi movido" : "não foram movidos"}`,
  },
  delete: {
    infinitive: "Deletar", gerund: "Deletando",
    done: (n) => plural(n, "deletado", "deletados"),
    notDone: "Não deletado",
    notDoneMany: (n) =>
      `${fileCount(n)} ${n === 1 ? "não foi deletado" : "não foram deletados"}`,
  },
};

export function batchResult(batch) {
  const { done, failed } = batch.progress;
  return `Lote concluído: ${VERBS[batch.kind].done(done)}, ` +
    `${number(failed)} com erro.`;
}

// Detalhes carregados só quando o card aparece na tela.

import { h, icon } from "./ui.js";

const THUMBNAIL_WIDTH = 240;
const CONCURRENCY = 4;
const IMAGES = new Set(["jpg", "jpeg", "png", "gif", "webp", "bmp", "avif"]);
const VIDEOS = new Set(["mp4", "webm", "mov", "m4v", "ogv"]);

// Executa `load(node)` quando o elemento fica visível, poucos por vez.
export class LazyLoader {
  constructor(load) {
    this.load = load;
    this.queue = [];
    this.running = 0;
    this.observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        this.observer.unobserve(entry.target);
        this.queue.push(entry.target);
      }
      this.pump();
    }, { rootMargin: "300px" });
  }

  observe(node) {
    this.observer.observe(node);
  }

  reset() {
    this.observer.disconnect();
    this.queue = [];
  }

  pump() {
    while (this.running < CONCURRENCY && this.queue.length > 0) {
      this.running += 1;
      Promise.resolve(this.load(this.queue.shift()))
        .catch(() => {})
        .finally(() => {
          this.running -= 1;
          this.pump();
        });
    }
  }
}

function extensionOf(name) {
  const dot = name.lastIndexOf(".");
  return dot > 0 ? name.slice(dot + 1).toLowerCase() : "";
}

// Ícone para imagens e vídeos; extensão para os demais arquivos.
export function placeholder(name) {
  const extension = extensionOf(name);
  if (IMAGES.has(extension) || VIDEOS.has(extension)) return icon("image");
  return extension
    ? h("strong", {}, extension.toUpperCase().slice(0, 5)) : icon("file");
}

// Devolve um elemento de prévia ou null quando o tipo não tem prévia.
// urls recebe os endereços temporários que precisam ser liberados depois.
export async function buildPreview(name, file, urls) {
  const extension = extensionOf(name);
  if (IMAGES.has(extension)) {
    const bitmap = await createImageBitmap(file, {
      resizeWidth: THUMBNAIL_WIDTH, resizeQuality: "low",
    });
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    canvas.getContext("2d").drawImage(bitmap, 0, 0);
    bitmap.close();
    return canvas;
  }
  if (VIDEOS.has(extension)) {
    const video = document.createElement("video");
    const url = URL.createObjectURL(file);
    urls.push(url);
    video.muted = true;
    video.preload = "metadata";
    video.src = `${url}#t=0.1`;
    return video;
  }
  return null;
}

export function releaseUrls(urls) {
  urls.splice(0).forEach((url) => URL.revokeObjectURL(url));
}

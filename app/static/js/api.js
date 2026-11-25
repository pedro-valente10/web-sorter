// Comunicação com o servidor. Só nomes e resultados, nunca conteúdo.

const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

export async function api(method, url, body) {
  const options = { method, headers: { "X-CSRF-Token": csrfToken } };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(`/api${url}`, options);
  } catch (error) {
    throw new Error("Não foi possível falar com o servidor.");
  }
  if (response.status === 401) {
    throw new Error("Sua sessão expirou. Entre de novo para continuar.");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Erro inesperado.");
  return data;
}

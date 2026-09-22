const BASE = "/api";

function formatDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Request failed";
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = formatDetail(body.detail ?? body);
    } catch {
      /* ignore non-JSON errors */
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  health: () => request("/health"),
  pantry: {
    list: () => request("/pantry"),
    create: (body) => request("/pantry", { method: "POST", body: JSON.stringify(body) }),
    update: (id, body) => request(`/pantry/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    remove: (id) => request(`/pantry/${id}`, { method: "DELETE" }),
    sample: () => request("/pantry/sample", { method: "POST" }),
  },
  recipes: {
    list: (q = "") => request(`/recipes${q ? `?q=${encodeURIComponent(q)}` : ""}`),
    get: (id) => request(`/recipes/${id}`),
    create: (body) => request("/recipes", { method: "POST", body: JSON.stringify(body) }),
    update: (id, body) => request(`/recipes/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    remove: (id) => request(`/recipes/${id}`, { method: "DELETE" }),
  },
  constraints: {
    get: () => request("/constraints"),
    save: (body) => request("/constraints", { method: "PUT", body: JSON.stringify(body) }),
  },
  suggest: (limit = 6) => request("/suggest", { method: "POST", body: JSON.stringify({ limit }) }),
};

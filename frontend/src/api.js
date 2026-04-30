const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

export function searchItems(query, options = {}) {
  const params = new URLSearchParams({
    q: query,
    limit: String(options.limit ?? 12),
    sort: options.sort ?? "name",
    market_only: String(options.marketOnly ?? true),
    published: String(options.published ?? true),
  });
  if (options.category) {
    params.set("category", options.category);
  }
  if (options.group) {
    params.set("group", options.group);
  }
  return request(`/api/items/search?${params.toString()}`);
}

export function compareItem(typeId) {
  const params = new URLSearchParams({ type_id: String(typeId) });
  return request(`/api/items/compare?${params.toString()}`);
}

export function getItemHistory(typeId, options = {}) {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 90),
  });
  if (options.hub) {
    params.set("hub", options.hub);
  }
  return request(`/api/items/${typeId}/history?${params.toString()}`);
}

export function listWatchlist() {
  return request("/watchlist");
}

export function createWatchlistItem(payload) {
  return request("/watchlist", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateWatchlistItem(id, payload) {
  return request(`/watchlist/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteWatchlistItem(id) {
  return request(`/watchlist/${id}`, {
    method: "DELETE",
  });
}

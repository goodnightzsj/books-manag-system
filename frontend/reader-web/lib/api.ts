const TOKEN_KEY = "books_reader_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(t: string): void {
  window.localStorage.setItem(TOKEN_KEY, t);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  const t = getToken();
  if (t) headers.set("Authorization", `Bearer ${t}`);
  const r = await fetch(`/api/v1${path}`, { ...init, headers });
  if (!r.ok) {
    const body = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText}: ${body}`);
  }
  if (r.status === 204) return undefined as T;
  return (await r.json()) as T;
}

export function bookStreamUrl(id: string): string {
  const t = getToken();
  const base = `/api/v1/files/stream/${id}`;
  return t ? `${base}?token=${encodeURIComponent(t)}` : base;
}

export const api = {
  login: (username: string, password: string) =>
    apiFetch<{ access_token: string }>(`/auth/login`, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  search: (q: string) =>
    apiFetch<{ items: any[]; total: number }>(
      `/books?q=${encodeURIComponent(q)}&page=1&page_size=30`,
    ),
  getBook: (id: string) => apiFetch<any>(`/books/${id}`),
  getProgress: (id: string) => apiFetch<any>(`/reading-progress/${id}`),
  putProgress: (id: string, body: any) =>
    apiFetch<any>(`/reading-progress/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  recent: () => apiFetch<{ items: any[]; total: number }>(`/reading-progress/recent`),
  listBookmarks: (bookId: string) =>
    apiFetch<{ items: any[]; total: number }>(`/books/${bookId}/bookmarks`),
  createBookmark: (bookId: string, body: any) =>
    apiFetch<any>(`/books/${bookId}/bookmarks`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteBookmark: (bookId: string, bookmarkId: string) =>
    apiFetch<void>(`/books/${bookId}/bookmarks/${bookmarkId}`, { method: "DELETE" }),
  listAnnotations: (bookId: string) =>
    apiFetch<{ items: any[]; total: number }>(`/books/${bookId}/annotations`),
  createAnnotation: (bookId: string, body: any) =>
    apiFetch<any>(`/books/${bookId}/annotations`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteAnnotation: (bookId: string, annotationId: string) =>
    apiFetch<void>(`/books/${bookId}/annotations/${annotationId}`, { method: "DELETE" }),
};

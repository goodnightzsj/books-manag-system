const TOKEN_KEY = "books_admin_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`/api/v1${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    apiFetch<{ access_token: string }>(`/auth/login`, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  me: () => apiFetch<{ id: string; username: string; role: string }>(`/auth/me`),
  listBooks: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)]),
    ).toString();
    return apiFetch<{ items: any[]; total: number; page: number; page_size: number }>(
      `/books${qs ? `?${qs}` : ""}`,
    );
  },
  getBook: (id: string) => apiFetch<any>(`/books/${id}`),
  updateBook: (id: string, body: any) =>
    apiFetch<any>(`/books/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteBook: (id: string) => apiFetch<void>(`/books/${id}`, { method: "DELETE" }),
  listCategories: () => apiFetch<any[]>(`/categories`),
  listCategoryBooks: (categoryId: string, page = 1, pageSize = 50) =>
    apiFetch<{ items: any[]; total: number; page: number; page_size: number }>(
      `/categories/${categoryId}/books?page=${page}&page_size=${pageSize}`,
    ),
  createCategory: (body: any) =>
    apiFetch<any>(`/categories`, { method: "POST", body: JSON.stringify(body) }),
  deleteCategory: (id: string) =>
    apiFetch<void>(`/categories/${id}`, { method: "DELETE" }),
  addBookToCategory: (categoryId: string, bookId: string) =>
    apiFetch<void>(`/categories/${categoryId}/books/${bookId}`, { method: "POST" }),
  removeBookFromCategory: (categoryId: string, bookId: string) =>
    apiFetch<void>(`/categories/${categoryId}/books/${bookId}`, { method: "DELETE" }),
  listScanJobs: (limit = 50) =>
    apiFetch<{ items: any[]; total: number }>(`/scanner/jobs?limit=${limit}`),
  trending: (limit = 6) =>
    apiFetch<any[]>(`/recommendations/trending?limit=${limit}`),
  getScanJob: (id: string) => apiFetch<any>(`/scanner/jobs/${id}`),
  listScanJobItems: (id: string) =>
    apiFetch<{ items: any[]; total: number }>(`/scanner/jobs/${id}/items`),
  startDirectoryScan: (directory: string) =>
    apiFetch<any>(`/scanner/jobs/directory`, {
      method: "POST",
      body: JSON.stringify({ directory }),
    }),
  retryFailed: (id: string) =>
    apiFetch<any>(`/scanner/jobs/${id}/retry-failed`, { method: "POST" }),
  queueMetadata: (bookId: string, force = false) =>
    apiFetch<any>(`/scanner/books/${bookId}/metadata-sync?force=${force}`, {
      method: "POST",
    }),
  queueCover: (bookId: string, preferRemote = false) =>
    apiFetch<any>(
      `/scanner/books/${bookId}/extract-cover?prefer_remote=${preferRemote}`,
      { method: "POST" },
    ),
};

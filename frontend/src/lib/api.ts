const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = "ApiError"; }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!API_URL) throw new ApiError(0, "The archive API has not been configured for this deployment. The website is online, but its backend service is not connected yet.");
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers: HeadersInit = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers };
  let res: Response;
  try { res = await fetch(`${API_URL}${path}`, { ...options, headers }); }
  catch { throw new ApiError(0, "Cannot reach the archive backend. Its production URL may be missing, or the backend service may be offline."); }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, detail.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  async upload<T>(path: string, file: File, meta: Record<string, unknown>): Promise<T> {
    const token = localStorage.getItem("access_token");
    const form = new FormData(); form.append("file", file); form.append("meta", JSON.stringify(meta));
    if (!API_URL) throw new ApiError(0, "The archive backend has not been configured for this deployment.");
    let res: Response;
    try { res = await fetch(`${API_URL}${path}`, { method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : {}, body: form }); }
    catch { throw new ApiError(0, "Cannot reach the archive backend. Check its production deployment."); }
    if (!res.ok) { const detail = await res.json().catch(() => ({ detail: res.statusText })); throw new ApiError(res.status, detail.detail ?? "Upload failed"); }
    return res.json() as Promise<T>;
  },
};
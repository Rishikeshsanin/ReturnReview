// Public URL used by the user's browser (including images and overlays).
export const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://returnreview-api-production.up.railway.app";

// Next.js server-side routes run inside the web container. In Docker,
// localhost:8000 refers to the web container, not the sibling API service.
// Configure this server-only value with Docker Compose's internal service DNS.
const INTERNAL_API = process.env.RETURNREVIEW_INTERNAL_API_BASE_URL;

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = typeof window === "undefined" && INTERNAL_API ? INTERNAL_API : API;
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body.detail || message;
    } catch {}
    throw new Error(message);
  }
  return res.json();
}

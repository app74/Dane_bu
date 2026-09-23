// Without VITE_API_URL the backend is expected on port 8000 of the host that served the page,
// so the same build works on localhost and from other PCs in the LAN. Vercel sets /api.
export const API =
  import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;
export const AUTH_REQUIRED_EVENT = "dane-auth-required";

export async function apiFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API}${path}`, init);
  if (response.status === 401) window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT));
  return response;
}

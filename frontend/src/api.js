// Single source of truth for the backend origin and for authenticated calls.
// Override the origin per environment with VITE_API_URL (see .env.example).
export const API_BASE = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const TOKEN_KEY = "accessToken";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function saveSession({ access_token, user }) {
  localStorage.setItem(TOKEN_KEY, access_token);
  localStorage.setItem("userId", user.user_id);
  localStorage.setItem("userName", user.user_name);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem("userId");
  localStorage.removeItem("userName");
}

/** Error carrying the HTTP status, so callers can tell 403 from a network blip. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function messageFromBody(body, fallback) {
  const detail = body && body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI validation errors arrive as a list of {loc, msg}.
    // Pydantic prefixes custom validator messages with "Value error, ".
    return (
      detail
        .map((d) => d.msg && d.msg.replace(/^Value error, /, ""))
        .filter(Boolean)
        .join(", ") || fallback
    );
  }
  return fallback;
}

/**
 * fetch() with the bearer token attached and errors normalised.
 *
 * On 401 the stored session is cleared and the page returns to the login
 * screen: the token is gone or expired, so nothing else will succeed either.
 */
export async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };

  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearSession();
    if (window.location.pathname !== "/") {
      window.location.assign("/");
    }
    throw new ApiError("Your session has expired. Please sign in again.", 401);
  }

  if (res.status === 204) return null;

  let body = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (!res.ok) {
    throw new ApiError(
      messageFromBody(body, `Request failed (${res.status})`),
      res.status
    );
  }

  return body;
}

export default API_BASE;

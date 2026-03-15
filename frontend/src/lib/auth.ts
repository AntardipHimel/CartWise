export type UserSession = {
  email: string;
  name: string;
};

const SESSION_KEY = "cartwise_session";
const ROUTE_CACHE_KEY = "cartwise_selected_routes";

export function getStoredSession(): UserSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as UserSession;
  } catch {
    return null;
  }
}

export function setStoredSession(session: UserSession) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(SESSION_KEY);
}

export function getCachedRoutes() {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(ROUTE_CACHE_KEY);
  if (!raw) return [];

  try {
    return JSON.parse(raw) as any[];
  } catch {
    return [];
  }
}

export function pushCachedRoute(route: any) {
  if (typeof window === "undefined") return;
  const existing = getCachedRoutes();
  const next = [route, ...existing].slice(0, 20);
  window.localStorage.setItem(ROUTE_CACHE_KEY, JSON.stringify(next));
}
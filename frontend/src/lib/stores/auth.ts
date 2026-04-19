import { writable, derived, get } from "svelte/store";
import { api } from "$lib/api/client";
import { fetchWorkspaces, selectWorkspace } from "./workspace";
import { loadSession, fetchSessions } from "./agent";

interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user_id: string;
  last_workspace_id: string | null;
}

export const user = writable<User | null>(null);
export const isAuthenticated = derived(user, ($user) => $user !== null);
export const isLoading = writable(false);
export const authError = writable<string | null>(null);
export const displayName = writable<string>("EoS");

export async function loadConfig() {
  try {
    const config = await api.getConfig();
    displayName.set(config.display_name);
  } catch {
    displayName.set("EoS");
  }
}

export async function login(username: string, password: string) {
  isLoading.set(true);
  authError.set(null);
  try {
    const response = await api.post<LoginResponse>("/auth/login", { username, password });
    api.setToken(response.access_token);
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", response.refresh_token);
    }
    const userData = await api.get<User>("/auth/me");
    user.set(userData);

    const workspaces = await fetchWorkspaces();
    if (workspaces.length === 0) {
      await api.post("/workspaces/", { name: "Default" });
      await fetchWorkspaces();
    }
    const lastWorkspaceId = response.last_workspace_id || (workspaces.length > 0 ? workspaces[0].id : null);
    if (lastWorkspaceId) {
      await selectWorkspace(lastWorkspaceId);
    }
  } catch (e: any) {
    authError.set(e.message || "Login failed");
    throw e;
  } finally {
    isLoading.set(false);
  }
}

export function logout() {
  user.set(null);
  api.logout();
}

export async function checkAuth() {
  const token = api.getTokenSync();
  if (!token) return;
  try {
    const userData = await api.get<User>("/auth/me");
    user.set(userData);

    const workspaces = await fetchWorkspaces();
    if (workspaces.length > 0) {
      const savedWorkspaceId = localStorage.getItem("last_workspace_id");
      const workspaceId = savedWorkspaceId || workspaces[0].id;
      await selectWorkspace(workspaceId);
      localStorage.setItem("last_workspace_id", workspaceId);
    }

    await fetchSessions();
    const sessionId = localStorage.getItem("last_session_id");
    const sessions = await api.getSessions();
    if (sessions.sessions.length > 0) {
      const targetSessionId = sessionId || sessions.sessions[0].id;
      await loadSession(targetSessionId);
      localStorage.setItem("last_session_id", targetSessionId);
    } else {
      const newSession = await api.createSession("Session 1");
      await loadSession(newSession.id);
      localStorage.setItem("last_session_id", newSession.id);
    }
  } catch {
    api.clearToken();
  }
}

export function mockLogin(username: string) {
  user.set({
    id: crypto.randomUUID(),
    email: `${username}@company.com`,
    display_name: username.charAt(0).toUpperCase() + username.slice(1),
    role: "trader",
    is_active: true,
  });
}

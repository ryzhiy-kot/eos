import { writable, derived } from "svelte/store";
import { api } from "$lib/api/client";

interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
}

export const user = writable<User | null>(null);
export const isAuthenticated = derived(user, ($user) => $user !== null);
export const isLoading = writable(false);
export const authError = writable<string | null>(null);

export async function login(username: string, password: string) {
  isLoading.set(true);
  authError.set(null);
  try {
    await api.login(username, password);
    const userData = await api.get<User>("/auth/me");
    user.set(userData);
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
  const token = api.getToken();
  if (!token) return;
  try {
    const userData = await api.get<User>("/auth/me");
    user.set(userData);
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

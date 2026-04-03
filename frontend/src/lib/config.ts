import { writable, get } from "svelte/store";

export interface MockConfig {
  enabled: boolean;
  dataDelay: number;
}

export const mockConfig = writable<MockConfig>({
  enabled: true,
  dataDelay: 0,
});

export function isMockEnabled(): boolean {
  if (typeof window === "undefined") return true;
  const stored = localStorage.getItem("mock_mode");
  if (stored === null) {
    localStorage.setItem("mock_mode", "true");
    return true;
  }
  return stored === "true" || get(mockConfig).enabled;
}

export function enableMockMode(enabled: boolean = true) {
  localStorage.setItem("mock_mode", String(enabled));
  mockConfig.update((c) => ({ ...c, enabled }));
}
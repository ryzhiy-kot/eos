export interface MockConfig {
  enabled: boolean;
  dataDelay: number;
}

export const mockConfig = writable<MockConfig>({
  enabled: true,
  dataDelay: 0,
});

export function isMockEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("mock_mode") === "true" || mockConfig.enabled;
}

export function enableMockMode(enabled: boolean = true) {
  localStorage.setItem("mock_mode", String(enabled));
  mockConfig.update((c) => ({ ...c, enabled }));
}

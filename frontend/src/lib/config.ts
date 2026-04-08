import { writable } from "svelte/store";

const MOCK_MODE = import.meta.env.VITE_MOCK_MODE ?? "true";

export interface MockConfig {
  enabled: boolean;
  dataDelay: number;
}

export const mockConfig = writable<MockConfig>({
  enabled: MOCK_MODE === "true",
  dataDelay: 0,
});

export function isMockEnabled(): boolean {
  return MOCK_MODE === "true";
}

import { vi } from "vitest";

Object.defineProperty(window, "crypto", {
  value: {
    randomUUID: () => Math.random().toString(36).substring(2, 15),
  },
});

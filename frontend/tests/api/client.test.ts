import { describe, it, expect, vi, beforeEach } from "vitest";

declare const global: {
  fetch: ReturnType<typeof vi.fn>;
};

const API_BASE = "/api";

class TestApiClient {
  private _token: string | null = null;

  constructor() {
    // Read initial token from localStorage
    this._token = localStorage.getItem("access_token");
  }

  private getToken(): string | null {
    // Always read fresh from localStorage to ensure we have the latest token
    this._token = localStorage.getItem("access_token");
    return this._token;
  }

  setToken(token: string) {
    this._token = token;
    localStorage.setItem("access_token", token);
  }

  clearToken() {
    this._token = null;
    localStorage.removeItem("access_token");
  }

  getTokenSync(): string | null {
    return this.getToken();
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || "Request failed");
    }

    return response.json();
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }

  post<T>(path: string, data: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async login(username: string, password: string) {
    const result = await this.post<{ access_token: string; refresh_token: string; expires_in: number }>(
      "/auth/login",
      { username, password }
    );
    this.setToken(result.access_token);
    return result;
  }

  getPanels() {
    return this.get<any[]>("/panels");
  }

  createPanel(panel: {
    artifact_id: string;
    name: string;
    bq_function: string;
    bq_params: object;
    refresh_interval: number;
  }) {
    return this.post<any>("/panels", panel);
  }
}

describe("ApiClient", () => {
  let client: TestApiClient;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    client = new TestApiClient();
  });

  describe("token management", () => {
    it("should initialize with token from localStorage", () => {
      localStorage.setItem("access_token", "test_token");
      const client = new TestApiClient();
      // After construction, token is cached but getToken() reads fresh
      expect(client.getTokenSync()).toBe("test_token");
    });

    it("should set token and save to localStorage", () => {
      const client = new TestApiClient();
      client.setToken("new_token");
      expect(client.getTokenSync()).toBe("new_token");
      expect(localStorage.getItem("access_token")).toBe("new_token");
    });

    it("should clear token and remove from localStorage", () => {
      const client = new TestApiClient();
      client.setToken("test_token");
      client.clearToken();
      expect(client.getTokenSync()).toBeNull();
      expect(localStorage.getItem("access_token")).toBeNull();
    });

    it("should read fresh token from localStorage on each request", async () => {
      // Set token initially
      const client = new TestApiClient();
      client.setToken("initial_token");
      
      // Simulate token being updated in localStorage (e.g., after refresh)
      localStorage.setItem("access_token", "updated_token");
      
      // Mock fetch to check what's being sent
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      });
      
      await client.get("/test");
      
      // Should use the updated token from localStorage, not cached one
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/test",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer updated_token",
          }),
        })
      );
    });
  });

  describe("authentication", () => {
    it("should login and set token on success", async () => {
      const mockResponse = {
        access_token: "jwt_token",
        refresh_token: "refresh_token",
        expires_in: 3600,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await client.login("trader", "trader123");

      expect(result.access_token).toBe("jwt_token");
      expect(client.getTokenSync()).toBe("jwt_token");
    });

    it("should throw error on login failure", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: "Invalid credentials" }),
      });

      await expect(client.login("bad", "creds")).rejects.toThrow("Invalid credentials");
    });
  });

  describe("API requests", () => {
    it("should include Authorization header when token is set", async () => {
      client.setToken("test_token");

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: "test" }),
      });

      await client.get("/test");

      expect(global.fetch).toHaveBeenCalledWith(
        "/api/test",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test_token",
          }),
        })
      );
    });

    it("should throw error on 401", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        status: 401,
        ok: false,
        json: () => Promise.resolve({ detail: "Unauthorized" }),
      });

      await expect(client.get("/protected")).rejects.toThrow("Unauthorized");
    });
  });

  describe("panel operations", () => {
    it("should get list of panels", async () => {
      const mockPanels = [{ id: "1", name: "Test Panel" }];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPanels),
      });

      const result = await client.getPanels();
      expect(result).toEqual(mockPanels);
    });

    it("should create a panel", async () => {
      const panelData = {
        artifact_id: "art-1",
        name: "My Panel",
        bq_function: "bq.pnl",
        bq_params: { desk: "FX" },
        refresh_interval: 60,
      };

      const mockPanel = { id: "panel-1", ...panelData };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPanel),
      });

      const result = await client.createPanel(panelData);
      expect(result).toEqual(mockPanel);
    });
  });
});

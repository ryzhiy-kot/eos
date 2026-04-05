const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
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

  // Auth
  async login(username: string, password: string) {
    const result = await this.post<{ access_token: string; refresh_token: string; expires_in: number }>(
      "/auth/login",
      { username, password }
    );
    this.setToken(result.access_token);
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", result.refresh_token);
    }
    return result;
  }

  logout() {
    this.clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  // Market
  getInstruments(params?: { asset_class?: string; search?: string }) {
    const query = new URLSearchParams();
    if (params?.asset_class) query.set("asset_class", params.asset_class);
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return this.get<any[]>(`/market/instruments${qs ? "?" + qs : ""}`);
  }

  getQuote(symbol: string) {
    return this.get<any>(`/market/quote/${symbol}`);
  }

  getOHLCV(symbol: string, days = 90) {
    return this.get<any[]>(`/market/ohlcv/${symbol}?days=${days}`);
  }

  // Risk
  getPortfolioRisk() {
    return this.get<any>("/risk/portfolio");
  }

  getVarHistory(days = 30) {
    return this.get<any[]>(`/risk/var-history?days=${days}`);
  }

  getPositions(params?: { desk?: string; strategy?: string }) {
    const query = new URLSearchParams();
    if (params?.desk) query.set("desk", params.desk);
    if (params?.strategy) query.set("strategy", params.strategy);
    const qs = query.toString();
    return this.get<any[]>(`/risk/positions${qs ? "?" + qs : ""}`);
  }

  // PnL
  getPnLAttribution() {
    return this.get<any>("/pnl/attribution");
  }

  // Agent
  async *agentChat(message: string, sessionId?: string, history?: Array<{role: string, content: string}>) {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const body: Record<string, unknown> = { message };
    if (sessionId) body.session_id = sessionId;
    if (history) body.history = history;

    const response = await fetch(`${API_BASE}/agents/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error("Agent request failed");
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    if (!reader) return;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.trim()) {
          try {
            yield JSON.parse(line);
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  }

  getConversations() {
    return this.get<any>("/agents/conversations");
  }

  getSessions() {
    return this.get<{ sessions: Array<{ id: string; name: string; created_at: string; updated_at: string }> }>("/agents/sessions");
  }

  getSessionArtifacts(sessionId: string) {
    return this.get<{ artifacts: any[] }>(`/agents/sessions/${sessionId}/artifacts`);
  }

  getSessionMessages(sessionId: string) {
    return this.get<{ messages: Array<{ id: string; session_id: string; role: string; content: string; created_at: string }> }>(`/agents/sessions/${sessionId}/messages`);
  }

  // Panels
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

  getPanelRefresh(panelId: string) {
    return this.get<{ data: unknown; last_updated: string }>(`/panels/${panelId}/refresh`);
  }

  deletePanel(panelId: string) {
    return this.request<void>(`/panels/${panelId}`, { method: "DELETE" });
  }

  updatePanel(panelId: string, updates: { name?: string; refresh_interval?: number }) {
    return this.request<any>(`/panels/${panelId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }
}

export const api = new ApiClient();

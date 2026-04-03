export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string = "";
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 2000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private isConnecting = false;

  connect(path: string) {
    if (this.isConnecting) return;
    this.isConnecting = true;
    this.url = path;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}${path}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.emit("connected", {});
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit(data.type || "message", data);
      } catch {
        // skip non-JSON messages
      }
    };

    this.ws.onclose = () => {
      this.isConnecting = false;
      this.emit("disconnected", {});
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.isConnecting = false;
    };
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(this.url), Math.min(delay, 30000));
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any) {
    this.listeners.get(event)?.forEach((cb) => cb(data));
  }

  disconnect() {
    this.maxReconnectAttempts = 0;
    this.ws?.close();
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export const wsManager = new WebSocketManager();

// API Client for Elyon Backend Communication

const API_BASE_URL = typeof window !== 'undefined'
    ? (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
    : 'http://localhost:8000';

interface ApiError {
    message: string;
    status: number;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const config: RequestInit = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error: ApiError = {
                    message: `API Error: ${response.statusText}`,
                    status: response.status,
                };
                throw error;
            }

            return await response.json();
        } catch (error) {
            // Handle network errors (connection refused, timeout, etc.)
            if (error instanceof TypeError) {
                throw {
                    message: `Network Error: Unable to connect to ${this.baseUrl}. Please check if the server is running.`,
                    status: 0,
                } as ApiError;
            }

            // Re-throw ApiError as-is
            if (error && typeof error === 'object' && 'status' in error) {
                throw error;
            }

            // Handle other errors
            if (error instanceof Error) {
                throw {
                    message: error.message,
                    status: 0,
                } as ApiError;
            }
            throw error;
        }
    }

    // Data Command APIs
    async plot(paneId: string, prompt: string): Promise<{ result: any }> {
        return this.request('/api/commands/plot', {
            method: 'POST',
            body: JSON.stringify({ pane_id: paneId, prompt }),
        });
    }

    async run(paneId: string, code: string): Promise<{ result: any }> {
        return this.request('/api/commands/run', {
            method: 'POST',
            body: JSON.stringify({ pane_id: paneId, code }),
        });
    }

    async diff(paneId1: string, paneId2: string): Promise<{ result: any }> {
        return this.request('/api/commands/diff', {
            method: 'POST',
            body: JSON.stringify({ pane_id_1: paneId1, pane_id_2: paneId2 }),
        });
    }

    async summarize(paneId: string): Promise<{ result: any }> {
        return this.request('/api/commands/summarize', {
            method: 'POST',
            body: JSON.stringify({ pane_id: paneId }),
        });
    }

    // Health check
    async health(): Promise<{ status: string }> {
        return this.request('/api/health');
    }
}

export const apiClient = new ApiClient();
export type { ApiError };

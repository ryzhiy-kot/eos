// API Client for monad Backend Communication

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

    // Infrastructure APIs
    async execute(request: {
        type: 'command' | 'chat';
        session_id: string;
        command_name?: string;
        args?: string[];
        action?: string;
        context_artifacts?: Record<string, any>;
        referenced_artifact_ids?: string[];
    }): Promise<{ success: boolean; result: any }> {
        return this.request('/api/v1/sessions/execute', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    // Session Management
    async listSessions(workspaceId: string): Promise<any[]> {
        return this.request(`/api/v1/sessions/workspace/${workspaceId}`);
    }

    async updateSession(sessionId: string, updates: { name?: string; is_active?: boolean }): Promise<any> {
        return this.request(`/api/v1/sessions/${sessionId}`, {
            method: 'PATCH',
            body: JSON.stringify(updates),
        });
    }

    // Health check
    async health(): Promise<{ status: string }> {
        return this.request('/api/v1/health');
    }

    async createArtifact(artifact: any): Promise<any> {
        return this.request('/api/v1/artifacts', {
            method: 'POST',
            body: JSON.stringify(artifact),
        });
    }

    // Auth
    async login(username: string): Promise<any> {
        return this.request('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username }),
        });
    }

    // Workspace
    async getWorkspace(id: string): Promise<any> {
        return this.request(`/api/v1/workspaces/${id}`);
    }

    async updateWorkspace(id: string, updates: any): Promise<any> {
        return this.request(`/api/v1/workspaces/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(updates),
        });
    }

    async updateActiveWorkspace(userId: string, workspaceId: string): Promise<any> {
        return this.request('/api/v1/auth/update-active-workspace', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, workspace_id: workspaceId }),
        });
    }

    async archivePane(workspaceId: string, paneData: any): Promise<any> {
        return this.request(`/api/v1/workspaces/${workspaceId}/archive-pane`, {
            method: 'POST',
            body: JSON.stringify(paneData),
        });
    }
}

export const apiClient = new ApiClient();
export type { ApiError };

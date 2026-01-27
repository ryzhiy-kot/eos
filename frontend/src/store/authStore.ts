import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
    isAuthenticated: boolean;
    user: string | null;
    active_workspace_id: string | null;
    error: string | null;
    isLoading: boolean;
    isHydrated: boolean;
    login: (u: string, p: string) => Promise<boolean>;
    logout: () => void;
    setHasHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            isAuthenticated: false,
            user: null,
            active_workspace_id: null,
            error: null,
            isLoading: false,
            isHydrated: false,

            login: async (username, password) => {
                set({ isLoading: true, error: null });

                try {
                    const { apiClient } = await import('../lib/apiClient');
                    const { workspaceActions } = await import('./workspaceStore');
                    const user = await apiClient.login(username);

                    if (user.memberships && user.memberships.length > 0) {
                        // Priority: active_workspace_id if valid, else first membership
                        const targetWs = user.active_workspace_id || user.memberships[0].workspace_id;
                        workspaceActions.setWorkspaceId(targetWs);
                    }

                    set({
                        isAuthenticated: true,
                        user: user.user_id,
                        active_workspace_id: user.active_workspace_id || null,
                        isLoading: false,
                        error: null
                    });
                    return true;
                } catch (err: any) {
                    set({
                        isLoading: false,
                        error: err.message || 'ACCESS DENIED: Invalid credentials.'
                    });
                    return false;
                }
            },

            logout: () => set({ isAuthenticated: false, user: null, active_workspace_id: null }),
            setHasHydrated: () => set({ isHydrated: true })
        }),
        {
            name: 'elyon-auth-storage',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                user: state.user,
                active_workspace_id: state.active_workspace_id
            }),
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated();
            }
        }
    )
);

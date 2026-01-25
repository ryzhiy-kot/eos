import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
    isAuthenticated: boolean;
    user: string | null;
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
                        workspaceActions.setWorkspaceId(user.memberships[0].workspace_id);
                    }

                    set({
                        isAuthenticated: true,
                        user: user.user_id,
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

            logout: () => set({ isAuthenticated: false, user: null }),
            setHasHydrated: () => set({ isHydrated: true })
        }),
        {
            name: 'elyon-auth-storage',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                user: state.user
            }),
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated();
            }
        }
    )
);

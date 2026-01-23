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

                // Mock API delay
                await new Promise(resolve => setTimeout(resolve, 800));

                if (username && password) {
                    set({
                        isAuthenticated: true,
                        user: username,
                        isLoading: false,
                        error: null
                    });
                    return true;
                } else {
                    set({
                        isLoading: false,
                        error: 'ACCESS DENIED: Invalid credentials.'
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

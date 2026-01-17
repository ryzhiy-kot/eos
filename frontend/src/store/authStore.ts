import { create } from 'zustand';

interface AuthState {
    isAuthenticated: boolean;
    user: string | null;
    error: string | null;
    isLoading: boolean;
    login: (u: string, p: string) => Promise<boolean>;
    logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    isAuthenticated: false,
    user: null,
    error: null,
    isLoading: false,

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

    logout: () => set({ isAuthenticated: false, user: null })
}));

/**
 * PROJECT: MONAD
 * AUTHOR: Kyrylo Yatsenko
 * YEAR: 2026
 * * COPYRIGHT NOTICE:
 * © 2026 Kyrylo Yatsenko. All rights reserved.
 * 
 * This work represents a proprietary methodology for Human-Machine Interaction (HMI).
 * All source code, logic structures, and User Experience (UX) frameworks
 * contained herein are the sole intellectual property of Kyrylo Yatsenko.
 * 
 * ATTRIBUTION REQUIREMENT:
 * Any use of this program, or any portion thereof (including code snippets and
 * interaction patterns), may not be used, redistributed, or adapted
 * without explicit, visible credit to Kyrylo Yatsenko as the original author.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '../lib/apiClient';

interface AuthState {
    isAuthenticated: boolean;
    user: string | null;
    active_workspace_id: string | null;
    sessionToken: string | null;
    error: string | null;
    isLoading: boolean;
    isHydrated: boolean;
    login: (u: string, p: string) => Promise<boolean>;
    logout: () => void;
    setHasHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            isAuthenticated: false,
            user: null,
            active_workspace_id: null,
            sessionToken: null,
            error: null,
            isLoading: false,
            isHydrated: false,

            login: async (username, password) => {
                set({ isLoading: true, error: null });

                try {
                    // Assuming login returns LoggedInUser which has session_token
                    const data = await apiClient.login(username, password);

                    set({
                        isAuthenticated: true,
                        user: data.user_id,
                        active_workspace_id: data.active_workspace_id || null,
                        sessionToken: data.session_token,
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

            logout: async () => {
                const token = get().sessionToken;
                if (token) {
                    try {
                        await apiClient.logout(token);
                    } catch (e) {
                        console.error("Logout failed", e);
                    }
                }
                set({ isAuthenticated: false, user: null, active_workspace_id: null, sessionToken: null });
            },
            setHasHydrated: () => set({ isHydrated: true })
        }),
        {
            name: 'monad-auth-storage',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                user: state.user,
                active_workspace_id: state.active_workspace_id,
                sessionToken: state.sessionToken
            }),
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated();
            }
        }
    )
);

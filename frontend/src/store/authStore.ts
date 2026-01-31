/**
 * PROJECT: EoS
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

interface AuthState {
    isAuthenticated: boolean;
    user: string | null;
    session_token: string | null;
    session_expires_at: string | null;
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
        (set, get) => ({
            isAuthenticated: false,
            user: null,
            session_token: null,
            session_expires_at: null,
            active_workspace_id: null,
            error: null,
            isLoading: false,
            isHydrated: false,

            login: async (username, password) => {
                set({ isLoading: true, error: null });

                try {
                    const { apiClient } = await import('../lib/apiClient');
                    const { workspaceActions } = await import('./workspaceStore');
                    const authResponse = await apiClient.login(username, password);

                    // Handle standard OAuth2 response or older format compatibility
                    const accessToken = authResponse.access_token || authResponse.session_token;
                    const user = authResponse.user || (authResponse.user_id ? authResponse : null);

                    if (!accessToken || !user) {
                         throw new Error("Invalid response from server");
                    }

                    if (user.memberships && user.memberships.length > 0) {
                        // Priority: active_workspace_id if valid, else first membership
                        const targetWs = user.active_workspace_id || user.memberships[0].workspace_id;
                        workspaceActions.setWorkspaceId(targetWs);
                    }

                    set({
                        isAuthenticated: true,
                        user: user.user_id,
                        session_token: accessToken,
                        session_expires_at: authResponse.session_expires_at || null,
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

            logout: async () => {
                const { session_token } = get();
                if (session_token) {
                    try {
                        const { apiClient } = await import('../lib/apiClient');
                        await apiClient.logout(session_token);
                    } catch (e) {
                        console.error('Logout failed:', e);
                    }
                }
                set({
                    isAuthenticated: false,
                    user: null,
                    session_token: null,
                    session_expires_at: null,
                    active_workspace_id: null
                });
            },
            setHasHydrated: () => set({ isHydrated: true })
        }),
        {
            name: 'eos-auth-storage',
            partialize: (state) => ({
                isAuthenticated: state.isAuthenticated,
                user: state.user,
                session_token: state.session_token,
                session_expires_at: state.session_expires_at,
                active_workspace_id: state.active_workspace_id
            }),
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated();
            }
        }
    )
);

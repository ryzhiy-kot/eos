import { useEffect, useRef } from 'react';
import { useWorkspaceStore, workspaceActions } from '../store/workspaceStore';
import { useAuthStore } from '../store/authStore';

export const useWorkspaceSync = () => {
    const isAuthenticated = useAuthStore(state => state.isAuthenticated);
    const hasInitialized = useRef(false);

    // Initial Load
    useEffect(() => {
        if (isAuthenticated && !hasInitialized.current) {
            workspaceActions.initializeWorkspace();
            hasInitialized.current = true;
        }
    }, [isAuthenticated]);

    // Auto-save on change
    useEffect(() => {
        if (!isAuthenticated || !hasInitialized.current) return;

        const timeout = setTimeout(() => {
            workspaceActions.syncWorkspace();
        }, 2000); // Debounce 2s

        return () => clearTimeout(timeout);
    }, [
        useWorkspaceStore(state => state.panes),
        useWorkspaceStore(state => state.activeLayout),
        useWorkspaceStore(state => state.density),
        isAuthenticated
    ]);
};

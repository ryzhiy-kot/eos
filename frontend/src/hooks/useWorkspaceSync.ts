import { useEffect, useRef } from 'react';
import { useWorkspaceStore, workspaceActions } from '../store/workspaceStore';
import { useAuthStore } from '../store/authStore';

export const useWorkspaceSync = () => {
    const isAuthenticated = useAuthStore(state => state.isAuthenticated);
    const activeWorkspaceId = useAuthStore(state => state.active_workspace_id);
    const isInitializing = useWorkspaceStore(state => state.isInitializing);
    const hasInitialized = useRef(false);

    // Initial Load
    useEffect(() => {
        if (isAuthenticated && !hasInitialized.current) {
            workspaceActions.initializeWorkspace(activeWorkspaceId);
            hasInitialized.current = true;
        }
    }, [isAuthenticated, activeWorkspaceId]);

    // Auto-save on change
    useEffect(() => {
        // block any sync if not authenticated, not initialized, OR currently initializing
        if (!isAuthenticated || !hasInitialized.current || isInitializing) return;

        const timeout = setTimeout(() => {
            workspaceActions.syncWorkspace();
        }, 2000); // Debounce 2s

        return () => clearTimeout(timeout);
    }, [
        useWorkspaceStore(state => state.panes),
        useWorkspaceStore(state => state.activeLayout),
        useWorkspaceStore(state => state.density),
        isAuthenticated,
        isInitializing
    ]);
};

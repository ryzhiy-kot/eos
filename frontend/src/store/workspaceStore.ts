import { create } from 'zustand';

export type PaneType = 'chat' | 'data' | 'doc' | 'visual' | 'code' | 'empty';

export interface PaneLineage {
    parentIds: string[];
    command: string;
    timestamp: string;
}

export interface Pane {
    id: string;
    type: PaneType;
    title: string;
    content: any; // Flexible content payload
    isSticky: boolean;
    lineage?: PaneLineage;
}

interface WorkspaceState {
    panes: Record<string, Pane>;
    activeLayout: string[]; // IDs of visible panes
    focusedPaneId: string | null;
    archive: string[]; // IDs of archived panes (shelf)
    density: 1 | 2 | 4 | 9; // User preference for max visible panes

    // Actions
    addPane: (pane: Pane) => void;
    removePane: (id: string) => void;
    focusPane: (id: string) => void;
    setDensity: (density: 1 | 2 | 4 | 9) => void;
    updatePaneContent: (id: string, content: any) => void;
    archivePane: (id: string) => void;
    restorePane: (id: string) => void;
    swapPanes: (id1: string, id2: string) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
    panes: {},
    activeLayout: [],
    focusedPaneId: null,
    archive: [],
    density: 4, // Default to quad view

    addPane: (pane) => set((state) => {
        // Logic: If layout is full, archive the oldest non-sticky pane
        const currentCount = state.activeLayout.length;
        let newLayout = [...state.activeLayout];
        let newArchive = [...state.archive];

        // If we haven't reached the current density limit, just add it
        if (currentCount < state.density) {
            newLayout.push(pane.id);
        } else {
            // We are full. Find a candidate to evict (not sticky, usually first one/LRU)
            // Simple strategy: Evict the first non-sticky pane
            const evictIndex = newLayout.findIndex(id => !state.panes[id]?.isSticky);

            if (evictIndex !== -1) {
                // Move to archive
                const evictedId = newLayout[evictIndex];
                newArchive.push(evictedId);
                // Replace with new pane or re-arrange? 
                // Spec says "auto-eviction", let's replace the slot or push to end if we treat layout as a queue.
                // Let's remove at index and push new one to end to maintain order
                newLayout.splice(evictIndex, 1);
                newLayout.push(pane.id);
            } else {
                // All are sticky? This is an edge case. For now, force add and maybe expand density if possible?
                // Or just replace the last one even if sticky (force)? 
                // Spec says "Cannot be overwritten or auto-evicted". 
                // We'll warn user? For now, we'll just push it and let the grid handle overflow or just replace 0?
                // Let's replace the first one for now as fallback.
                newLayout.shift();
                newLayout.push(pane.id);
            }
        }

        return {
            panes: { ...state.panes, [pane.id]: pane },
            activeLayout: newLayout,
            archive: newArchive,
            focusedPaneId: pane.id, // Auto-focus new pane
        };
    }),

    removePane: (id) => set((state) => {
        const { [id]: removed, ...remainingPanes } = state.panes;
        return {
            panes: remainingPanes,
            activeLayout: state.activeLayout.filter(pid => pid !== id),
            archive: state.archive.filter(pid => pid !== id),
            focusedPaneId: state.focusedPaneId === id ? null : state.focusedPaneId,
        };
    }),

    focusPane: (id) => set({ focusedPaneId: id }),

    setDensity: (density) => set((state) => {
        // If reducing density, we might need to archive excess panes
        // This is complex, will implement basic truncation for now
        let newLayout = [...state.activeLayout];
        let newArchive = [...state.archive];

        if (newLayout.length > density) {
            const excess = newLayout.length - density;
            const toArchive = newLayout.slice(0, excess);
            newLayout = newLayout.slice(excess);
            newArchive.push(...toArchive);
        }

        return {
            density,
            activeLayout: newLayout,
            archive: newArchive
        };
    }),

    updatePaneContent: (id, content) => set((state) => ({
        panes: {
            ...state.panes,
            [id]: { ...state.panes[id], content }
        }
    })),

    archivePane: (id) => set((state) => ({
        activeLayout: state.activeLayout.filter(pid => pid !== id),
        archive: [...state.archive, id]
    })),

    restorePane: (id) => set((state) => {
        return {
            archive: state.archive.filter(pid => pid !== id),
            activeLayout: [...state.activeLayout, id]
        };
    }),

    swapPanes: (id1, id2) => set((state) => {
        const layout = [...state.activeLayout];
        const idx1 = layout.indexOf(id1);
        const idx2 = layout.indexOf(id2);

        if (idx1 === -1 || idx2 === -1) return {};

        layout[idx1] = id2;
        layout[idx2] = id1;

        return { activeLayout: layout };
    })
}));

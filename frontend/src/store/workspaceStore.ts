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
    content: any;
    isSticky: boolean;
    lineage?: PaneLineage;
}

export interface ClockConfig {
    id: string;
    city: string; // e.g., 'New York', 'Tokyo'
    timezone: string; // e.g., 'America/New_York'
}

export interface TimerConfig {
    id: string;
    label: string;
    durationSec: number;
    endsAt: number; // Timestamp
}

interface WorkspaceState {
    panes: Record<string, Pane>; // All panes (active + archived)
    activeLayout: string[]; // IDs of visible panes
    focusedPaneId: string | null;
    archive: string[]; // IDs of archived panes (shelf)
    density: 1 | 2 | 4 | 9;

    // History (Simple stack of snapshots for undo/redo on key panes)
    // Map of PaneID -> Stack of Content
    history: Record<string, any[]>;
    future: Record<string, any[]>;

    // Utilities
    clocks: ClockConfig[];
    timers: TimerConfig[];
    isArchiveOpen: boolean; // For visual catalog overlay
    isHelpOpen: boolean;
    pendingCommand: string | null;

    // Actions
    addPane: (pane: Pane) => void;
    removePane: (id: string) => void;
    focusPane: (id: string) => void;
    setDensity: (density: 1 | 2 | 4 | 9) => void;
    updatePaneContent: (id: string, content: any, pushToHistory?: boolean) => void;

    // Archive Actions
    archivePane: (id: string) => void;
    restorePane: (id: string) => void;
    swapPanes: (id1: string, id2: string) => void;
    toggleArchiveOverlay: (isOpen?: boolean) => void;
    toggleHelpOverlay: (isOpen?: boolean) => void;
    setPendingCommand: (cmd: string | null) => void;

    // History Actions
    undoPane: (id: string) => void;
    redoPane: (id: string) => void;

    // Utility Actions
    addClock: (city: string, timezone: string) => void;
    removeClock: (id: string) => void;
    addTimer: (label: string, durationSec: number) => void;
    removeTimer: (id: string) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
    panes: {},
    activeLayout: [],
    focusedPaneId: null,
    archive: [],
    density: 4,
    history: {},
    future: {},
    clocks: [
        { id: 'c1', city: 'NYC', timezone: 'America/New_York' },
        { id: 'c2', city: 'LON', timezone: 'Europe/London' },
        { id: 'c3', city: 'TKY', timezone: 'Asia/Tokyo' },
    ],
    timers: [],
    isArchiveOpen: false,
    isHelpOpen: false,
    pendingCommand: null,

    addPane: (pane) => set((state) => {
        const currentCount = state.activeLayout.length;
        let newLayout = [...state.activeLayout];
        let newArchive = [...state.archive];

        if (currentCount < state.density) {
            newLayout.push(pane.id);
        } else {
            const evictIndex = newLayout.findIndex(id => !state.panes[id]?.isSticky);
            if (evictIndex !== -1) {
                const evictedId = newLayout[evictIndex];
                newArchive.push(evictedId);
                newLayout.splice(evictIndex, 1);
                newLayout.push(pane.id);
            } else {
                newLayout.shift();
                newLayout.push(pane.id);
            }
        }

        return {
            panes: { ...state.panes, [pane.id]: pane },
            activeLayout: newLayout,
            archive: newArchive,
            focusedPaneId: pane.id,
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
        let newLayout = [...state.activeLayout];
        let newArchive = [...state.archive];

        if (newLayout.length > density) {
            const excess = newLayout.length - density;
            const toArchive = newLayout.slice(0, excess);
            newLayout = newLayout.slice(excess);
            newArchive.push(...toArchive);
        }
        // If density increases, we could auto-restore from archive? (Spec doesn't explicitly mandate, but nice to have)
        // For now, strict: only archive on shrink.

        return {
            density,
            activeLayout: newLayout,
            archive: newArchive
        };
    }),

    updatePaneContent: (id, content, pushToHistory = true) => set((state) => {
        const currentContent = state.panes[id]?.content;
        const newHistory = { ...state.history };
        const newFuture = { ...state.future };

        if (pushToHistory) {
            if (!newHistory[id]) newHistory[id] = [];
            newHistory[id].push(currentContent);
            // Clear future on new change
            newFuture[id] = [];
        }

        return {
            panes: {
                ...state.panes,
                [id]: { ...state.panes[id], content }
            },
            history: newHistory,
            future: newFuture
        };
    }),

    archivePane: (id) => set((state) => ({
        activeLayout: state.activeLayout.filter(pid => pid !== id),
        archive: [...state.archive, id]
    })),

    restorePane: (id) => set((state) => {
        // If already active, just focus
        if (state.activeLayout.includes(id)) {
            return { focusedPaneId: id, isArchiveOpen: false };
        }

        // Need to verify capacity
        let newLayout = [...state.activeLayout];
        let newArchive = state.archive.filter(pid => pid !== id);

        if (newLayout.length >= state.density) {
            // Evict one to make room
            const evictIndex = newLayout.findIndex(pid => !state.panes[pid]?.isSticky);
            if (evictIndex !== -1) {
                const evictId = newLayout[evictIndex];
                newArchive.push(evictId);
                newLayout.splice(evictIndex, 1);
            } else {
                // Force replace first
                const evictId = newLayout[0];
                newArchive.push(evictId);
                newLayout.shift();
            }
        }
        newLayout.push(id);

        return {
            activeLayout: newLayout,
            archive: newArchive,
            focusedPaneId: id,
            isArchiveOpen: false
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
    }),

    toggleArchiveOverlay: (isOpen) => set((state) => ({
        isArchiveOpen: isOpen !== undefined ? isOpen : !state.isArchiveOpen,
        isHelpOpen: false // Close help if archive opens
    })),

    toggleHelpOverlay: (isOpen) => set((state) => ({
        isHelpOpen: isOpen !== undefined ? isOpen : !state.isHelpOpen,
        isArchiveOpen: false // Close archive if help opens
    })),

    setPendingCommand: (cmd) => set({ pendingCommand: cmd }),

    undoPane: (id) => set((state) => {
        const past = state.history[id] || [];
        if (past.length === 0) return {};

        const previous = past[past.length - 1];
        const newPast = past.slice(0, -1);
        const current = state.panes[id]?.content;

        const newFuture = { ...state.future };
        if (!newFuture[id]) newFuture[id] = [];
        newFuture[id].push(current);

        return {
            panes: { ...state.panes, [id]: { ...state.panes[id], content: previous } },
            history: { ...state.history, [id]: newPast },
            future: newFuture
        };
    }),

    redoPane: (id) => set((state) => {
        const future = state.future[id] || [];
        if (future.length === 0) return {};

        const next = future[future.length - 1];
        const newFuture = future.slice(0, -1);
        const current = state.panes[id]?.content;

        const newHistory = { ...state.history };
        if (!newHistory[id]) newHistory[id] = [];
        newHistory[id].push(current);

        return {
            panes: { ...state.panes, [id]: { ...state.panes[id], content: next } },
            history: newHistory,
            future: { ...state.future, [id]: newFuture }
        };
    }),

    addClock: (city, timezone) => set((state) => ({
        clocks: [...state.clocks, { id: `c_${Date.now()}`, city, timezone }]
    })),

    removeClock: (id) => set((state) => ({
        clocks: state.clocks.filter(c => c.id !== id)
    })),

    addTimer: (label, durationSec) => set((state) => ({
        timers: [...state.timers, {
            id: `t_${Date.now()}`,
            label,
            durationSec,
            endsAt: Date.now() + (durationSec * 1000)
        }]
    })),

    removeTimer: (id) => set((state) => ({
        timers: state.timers.filter(t => t.id !== id)
    })),
}));

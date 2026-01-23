import { create } from 'zustand';
import { CommandEntry } from '../lib/commandRegistry';

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
    isOverlayOpen: boolean;
    notifications: Array<{ id: string, message: string, type: 'error' | 'success' | 'info' }>;
    pendingCommand: string | null;
    commands: CommandEntry[];

    terminalFocusCounter: number;
    commandSubmitRequest: { command: string; timestamp: number } | null;
}

export const useWorkspaceStore = create<WorkspaceState>(() => ({
    panes: {},
    activeLayout: [],
    focusedPaneId: null,
    archive: [],
    density: 9,
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
    isOverlayOpen: false,
    notifications: [],
    pendingCommand: null,
    commands: [],

    terminalFocusCounter: 0,
    commandSubmitRequest: null,
}));

/**
 * standalone actions that modify the store.
 * These are NOT part of the store state, keeping the store data-only.
 * These should ideally be called ONLY by command handlers.
 */
export const workspaceActions = {
    triggerFocusTerminal: () =>
        useWorkspaceStore.setState((state) => ({ terminalFocusCounter: state.terminalFocusCounter + 1 })),

    triggerSubmitCommand: (command: string) =>
        useWorkspaceStore.setState({ commandSubmitRequest: { command, timestamp: Date.now() } }),

    addPane: (pane: Pane) => useWorkspaceStore.setState((state) => {
        // If already in active layout, just focus it and update content
        if (state.activeLayout.includes(pane.id)) {
            return {
                panes: { ...state.panes, [pane.id]: pane },
                focusedPaneId: pane.id
            };
        }

        let newLayout = [...state.activeLayout];
        let newArchive = state.archive.filter(id => id !== pane.id);

        if (newLayout.length < state.density) {
            newLayout.push(pane.id);
        } else {
            const evictIndex = newLayout.findIndex(id => !state.panes[id]?.isSticky);
            if (evictIndex !== -1) {
                const evictedId = newLayout[evictIndex];
                newArchive.push(evictedId);
                newLayout.splice(evictIndex, 1);
                newLayout.push(pane.id);
            } else {
                const evictedId = newLayout.shift();
                if (evictedId) newArchive.push(evictedId);
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

    removePane: (id: string) => useWorkspaceStore.setState((state) => {
        const { [id]: removed, ...remainingPanes } = state.panes;
        return {
            panes: remainingPanes,
            activeLayout: state.activeLayout.filter(pid => pid !== id),
            archive: state.archive.filter(pid => pid !== id),
            focusedPaneId: state.focusedPaneId === id ? null : state.focusedPaneId,
        };
    }),

    focusPane: (id: string) => useWorkspaceStore.setState({ focusedPaneId: id }),

    setDensity: (density: 1 | 2 | 4 | 9) => useWorkspaceStore.setState((state) => {
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

    updatePaneContent: (id: string, content: any, pushToHistory = true) => useWorkspaceStore.setState((state) => {
        const currentContent = state.panes[id]?.content;
        const newHistory = { ...state.history };
        const newFuture = { ...state.future };

        if (pushToHistory) {
            if (!newHistory[id]) newHistory[id] = [];
            newHistory[id].push(currentContent);
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

    renamePane: (id: string, title: string) => useWorkspaceStore.setState((state) => ({
        panes: {
            ...state.panes,
            [id]: { ...state.panes[id], title }
        }
    })),

    archivePane: (id: string) => useWorkspaceStore.setState((state) => ({
        activeLayout: state.activeLayout.filter(pid => pid !== id),
        archive: [...state.archive, id]
    })),

    restorePane: (id: string) => useWorkspaceStore.setState((state) => {
        if (state.activeLayout.includes(id)) {
            return { focusedPaneId: id, isArchiveOpen: false, isOverlayOpen: false };
        }

        let newLayout = [...state.activeLayout];
        let newArchive = state.archive.filter(pid => pid !== id);

        if (newLayout.length >= state.density) {
            const evictIndex = newLayout.findIndex(pid => !state.panes[pid]?.isSticky);
            if (evictIndex !== -1) {
                const evictId = newLayout[evictIndex];
                newArchive.push(evictId);
                newLayout.splice(evictIndex, 1);
            } else {
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

    swapPanes: (id1: string, id2: string) => useWorkspaceStore.setState((state) => {
        const layout = [...state.activeLayout];
        const idx1 = layout.indexOf(id1);
        const idx2 = layout.indexOf(id2);
        if (idx1 === -1 || idx2 === -1) return {};
        layout[idx1] = id2;
        layout[idx2] = id1;
        return { activeLayout: layout };
    }),

    toggleArchiveOverlay: (isOpen?: boolean) => useWorkspaceStore.setState((state) => {
        const nextOpen = isOpen !== undefined ? isOpen : !state.isArchiveOpen;
        return {
            isArchiveOpen: nextOpen,
            isHelpOpen: false,
            isOverlayOpen: nextOpen
        };
    }),

    toggleHelpOverlay: (isOpen?: boolean) => useWorkspaceStore.setState((state) => {
        const nextOpen = isOpen !== undefined ? isOpen : !state.isHelpOpen;
        return {
            isHelpOpen: nextOpen,
            isArchiveOpen: false,
            isOverlayOpen: nextOpen
        };
    }),

    setPendingCommand: (cmd: string | null) => useWorkspaceStore.setState({ pendingCommand: cmd }),

    undoPane: (id: string) => useWorkspaceStore.setState((state) => {
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

    redoPane: (id: string) => useWorkspaceStore.setState((state) => {
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

    addClock: (city: string, timezone: string) => useWorkspaceStore.setState((state) => ({
        clocks: [...state.clocks, { id: `c_${Date.now()}`, city, timezone }]
    })),

    removeClock: (id: string) => useWorkspaceStore.setState((state) => ({
        clocks: state.clocks.filter(c => c.id !== id)
    })),

    addTimer: (label: string, durationSec: number) => useWorkspaceStore.setState((state) => ({
        timers: [...state.timers, {
            id: `t_${Date.now()}`,
            label,
            durationSec,
            endsAt: Date.now() + (durationSec * 1000)
        }]
    })),

    removeTimer: (id: string) => useWorkspaceStore.setState((state) => ({
        timers: state.timers.filter(t => t.id !== id)
    })),

    registerCommands: (entries: CommandEntry[]) => useWorkspaceStore.setState((state) => {
        const newCommands = [...state.commands];
        entries.forEach(entry => {
            const idx = newCommands.findIndex(c => c.name === entry.name);
            if (idx !== -1) {
                newCommands[idx] = entry;
            } else {
                newCommands.push(entry);
            }
        });
        return { commands: newCommands };
    }),

    addNotification: (message: string, type: 'error' | 'success' | 'info' = 'info') =>
        useWorkspaceStore.setState((state) => ({
            notifications: [...state.notifications, { id: `notif_${Date.now()}_${Math.random()}`, message, type }]
        })),

    clearNotification: (id?: string) => useWorkspaceStore.setState((state) => ({
        notifications: id ? state.notifications.filter(n => n.id !== id) : []
    })),
};

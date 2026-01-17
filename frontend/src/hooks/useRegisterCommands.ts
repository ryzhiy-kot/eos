import { useEffect } from 'react';
import { useWorkspaceStore, workspaceActions } from '../store/workspaceStore';
import { useAuthStore } from '../store/authStore';
import { CommandEntry } from '../lib/commandRegistry';
import { parseDurationExpression } from '../lib/terminalUtils';
import { useCommandHandler } from './useCommandHandler';
import { COMMAND_NAMES } from '../lib/commandBus';

export const useRegisterCommands = () => {
    const { panes, activeLayout } = useWorkspaceStore();

    // --- Command Implementations (Subscribers) ---


    // --- Command Implementations (Subscribers) ---

    useCommandHandler(COMMAND_NAMES.GRID, (payload) => {
        const d = parseInt(payload.args[0]);
        if ([1, 2, 4, 9].includes(d)) {
            workspaceActions.setDensity(d as 1 | 2 | 4 | 9);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.FOCUS, (payload) => {
        const rawTarget = payload.args[0] || payload.context.sourceId;
        const target = rawTarget?.toUpperCase();
        if (target && panes[target]) {
            workspaceActions.focusPane(target);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.SWAP, (payload) => {
        if (payload.context.sourceId && payload.args[0]) {
            workspaceActions.swapPanes(payload.context.sourceId, payload.args[0].toUpperCase());
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.CLOSE, (payload) => {
        if (payload.context.sourceId) {
            workspaceActions.archivePane(payload.context.sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.HIDE, (payload) => {
        if (payload.context.sourceId) {
            workspaceActions.archivePane(payload.context.sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.LS, (payload) => {
        const isOpen = payload.args[0] === 'close' ? false : true;
        workspaceActions.toggleArchiveOverlay(isOpen);
        return true;
    });

    useCommandHandler(COMMAND_NAMES.SHOW, (payload) => {
        const rid = (payload.args[0] || payload.context.sourceId)?.toUpperCase();
        if (rid) {
            workspaceActions.restorePane(rid);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.UNDO, (payload) => {
        if (payload.context.sourceId) {
            workspaceActions.undoPane(payload.context.sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.REDO, (payload) => {
        if (payload.context.sourceId) {
            workspaceActions.redoPane(payload.context.sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.CLOCK, (payload) => {
        if (payload.args.length >= 2) {
            workspaceActions.addClock(payload.args[0], payload.args[1]);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.TIMER, (payload) => {
        if (payload.args.length > 0) {
            const { seconds, labelStartIdx } = parseDurationExpression(payload.args);
            const label = payload.args.slice(labelStartIdx).join(' ') || 'Timer';
            if (seconds > 0) {
                workspaceActions.addTimer(label, seconds);
                return true;
            }
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.HELP, (payload) => {
        const isOpen = payload.args[0] === 'close' ? false : true;
        workspaceActions.toggleHelpOverlay(isOpen);
        return true;
    });

    useCommandHandler(COMMAND_NAMES.QUESTION, () => {
        workspaceActions.toggleHelpOverlay(true);
        return true;
    });

    useCommandHandler(COMMAND_NAMES.RENAME, (payload) => {
        const potentialId = payload.args[0]?.toUpperCase();
        if (potentialId && panes[potentialId] && payload.args.length > 1) {
            const newTitle = payload.args.slice(1).join(' ');
            workspaceActions.renamePane(potentialId, newTitle);
            return true;
        }
        if (payload.context.sourceId && payload.args.length > 0) {
            const newTitle = payload.args.join(' ');
            workspaceActions.renamePane(payload.context.sourceId, newTitle);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.LOGOUT, () => {
        useAuthStore.getState().logout();
        return true;
    });

    useCommandHandler(COMMAND_NAMES.REMOVE_PANE, (payload) => {
        const id = (payload.args[0] || payload.context.sourceId)?.toUpperCase();
        if (id) {
            workspaceActions.removePane(id);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.REMOVE_CLOCK, (payload) => {
        if (payload.args[0]) {
            workspaceActions.removeClock(payload.args[0]);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.REMOVE_TIMER, (payload) => {
        if (payload.args[0]) {
            workspaceActions.removeTimer(payload.args[0]);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.INIT, () => {
        if (activeLayout.length === 0) {
            workspaceActions.addPane({
                id: 'P1',
                type: 'chat',
                title: 'System Initialized',
                content: [{ role: 'system', content: 'Welcome to Elyon. System ready.' }],
                isSticky: true,
                lineage: { parentIds: [], command: 'init', timestamp: new Date().toISOString() }
            });
            return true;
        }
        return false;
    });

    // --- UI Control Handlers ---

    useCommandHandler(COMMAND_NAMES.UI_HELP, (payload) => {
        const isOpen = payload.args[0] === 'close' ? false : true;
        workspaceActions.toggleHelpOverlay(isOpen);
        return true;
    });

    useCommandHandler(COMMAND_NAMES.UI_ARCHIVE, (payload) => {
        const isOpen = payload.args[0] === 'close' ? false : true;
        workspaceActions.toggleArchiveOverlay(isOpen);
        return true;
    });

    useCommandHandler(COMMAND_NAMES.UI_PENDING_SET, (payload) => {
        workspaceActions.setPendingCommand(payload.args[0] || null);
        return true;
    });

    // --- Command Metadata Registration ---

    useEffect(() => {
        workspaceActions.registerCommands([
            {
                name: COMMAND_NAMES.LOAD,
                description: 'Load a file (PDF, CSV, JSON) into a new pane.',
                parameters: [{ name: 'file', description: 'File to load', required: false, type: 'file' }],
                category: 'system',
                shortcut: 'alt+o',
            },
            {
                name: COMMAND_NAMES.GRID,
                description: 'Set the number of visible panes.',
                parameters: [{ name: '1|2|4|9', description: 'Number of panes', required: false, type: 'number' }],
                category: 'system',
            },
            {
                name: COMMAND_NAMES.FOCUS,
                description: 'Switch focus to a specific pane.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to focus', required: false, type: 'paneId' }],
                category: 'pane',
                shortcut: 'ctrl+`',
            },
            {
                name: COMMAND_NAMES.SWAP,
                description: 'Swap the positions of two panes.',
                parameters: [{ name: 'P1', description: 'First pane ID', required: true, type: 'paneId' }, { name: 'P2', description: 'Second pane ID', required: true, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.CLOSE,
                description: 'Archive a pane (alias for /hide).',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to close', required: false, type: 'paneId' }],
                category: 'pane',
                shortcut: 'alt+w',
            },
            {
                name: COMMAND_NAMES.HIDE,
                description: 'Archive a pane (alias for /close).',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to hide', required: false, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.LS,
                description: 'Open the Archive Gallery (The Shelf).',
                category: 'utility',
                shortcut: 'alt+l',
            },
            {
                name: COMMAND_NAMES.SHOW,
                description: 'Restore a pane from the archive.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to restore', required: true, type: 'paneId' }],
                category: 'utility',
            },
            {
                name: COMMAND_NAMES.UNDO,
                description: 'Undo the last change in a pane.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to undo', required: false, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.REDO,
                description: 'Redo the last undone change.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to redo', required: false, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.CLOCK,
                description: 'Add a world clock to the header.',
                parameters: [{ name: 'City', description: 'City name', required: true }, { name: 'Zone', description: 'Timezone identifier', required: true }],
                category: 'utility',
            },
            {
                name: COMMAND_NAMES.TIMER,
                description: 'Start a countdown timer.',
                parameters: [{ name: 'Sec', description: 'Duration in seconds', required: true, type: 'number' }, { name: 'Label', description: 'Timer label', required: false }],
                category: 'utility',
            },
            {
                name: COMMAND_NAMES.HELP,
                description: 'Show command help.',
                category: 'utility',
                shortcut: 'ctrl+/',
            },
            {
                name: COMMAND_NAMES.RENAME,
                description: 'Rename a pane.',
                parameters: [{ name: 'PaneID', description: 'ID of pane to rename (optional)', required: false, type: 'paneId' }, { name: 'Name', description: 'New title', required: true }],
                category: 'pane',
                shortcut: 'alt+r',
            },
            {
                name: COMMAND_NAMES.LOGOUT,
                description: 'Log out of the system.',
                category: 'system',
                shortcut: 'alt+q',
            },
            {
                name: COMMAND_NAMES.QUESTION,
                description: 'Show command help (alias for /help).',
                category: 'utility',
                shortcut: 'shift+?',
            },
            // Data/Mock commands
            { name: COMMAND_NAMES.PLOT, description: 'Generate a chart from data.', example: '/plot [P1] "prompt"', category: 'data', shortcut: 'alt+p' },
            { name: COMMAND_NAMES.RUN, description: 'Execute code against pane data.', example: '/run [P1] "code"', category: 'data', shortcut: 'alt+x' },
            { name: COMMAND_NAMES.DIFF, description: 'Compare two panes.', example: '/diff [P1],[P2]', category: 'data', shortcut: 'alt+d' },
            { name: COMMAND_NAMES.SUMMARIZE, description: 'Summarize pane content.', example: '/summarize [P1]', category: 'data', shortcut: 'alt+s' },
        ] as CommandEntry[]);
    }, []); // Static registry, run once
};

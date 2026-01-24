import { useEffect } from 'react';
import { useWorkspaceStore, workspaceActions } from '../store/workspaceStore';
import { useAuthStore } from '../store/authStore';
import { CommandEntry } from '../lib/commandRegistry';
import { parseDurationExpression } from '../lib/terminalUtils';
import { COMMAND_NAMES } from '../lib/commandBus';
import { useCommandHandler } from './useCommandHandler';

export const useRegisterCommands = (onReady?: () => void) => {
    const panes = useWorkspaceStore(state => state.panes);
    const activeLayout = useWorkspaceStore(state => state.activeLayout);

    useEffect(() => {
        if (onReady) {
            onReady();
        }
    }, []);

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
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId && payload.args[0]) {
            workspaceActions.swapPanes(sourceId, payload.args[0].toUpperCase());
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.CLOSE, (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId) {
            workspaceActions.archivePane(sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.HIDE, (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId) {
            workspaceActions.archivePane(sourceId);
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
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId) {
            workspaceActions.undoPane(sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.REDO, (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId) {
            workspaceActions.redoPane(sourceId);
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
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId && payload.args.length > 0) {
            const newTitle = payload.args.join(' ');
            workspaceActions.renamePane(sourceId, newTitle);
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

    useCommandHandler(COMMAND_NAMES.CHAT, (payload) => {
        const initialMessage = payload.action || 'Hello';
        const targetId = payload.targetId && /^P\d+$/.test(payload.targetId) ? payload.targetId : undefined;

        const newPaneId = targetId || `P${Object.keys(useWorkspaceStore.getState().panes).length + 1}`;

        workspaceActions.addPane({
            id: newPaneId,
            type: 'chat',
            title: `Chat: ${initialMessage.substring(0, 20)}...`,
            content: [{ role: 'user', content: initialMessage }],
            isSticky: false,
            lineage: {
                parentIds: payload.context.sourceId ? [payload.context.sourceId] : [],
                command: payload.original || '/chat',
                timestamp: new Date().toISOString()
            }
        });

        // Mock response
        setTimeout(() => {
            const currentPane = useWorkspaceStore.getState().panes[newPaneId];
            if (currentPane) {
                const response = {
                    role: 'assistant',
                    content: `I've initialized the session. Context link to ${payload.context.sourceId || 'None'} verified.`
                };
                workspaceActions.updatePaneContent(newPaneId, [...currentPane.content, response]);
            }
        }, 800);

        return true;
    });

    useCommandHandler(COMMAND_NAMES.CLIP, (payload) => {
        const targetId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!targetId) {
            workspaceActions.addNotification('No target pane identified for clipping.', 'error');
            return false;
        }

        const pane = useWorkspaceStore.getState().panes[targetId];
        if (!pane) {
            workspaceActions.addNotification(`Pane ${targetId} not found.`, 'error');
            return false;
        }

        let clipboardContent = '';
        let formatLabel = 'Text';

        try {
            switch (pane.type) {
                case 'chat':
                    clipboardContent = JSON.stringify({
                        chat_name: pane.title,
                        history: pane.content
                    }, null, 2);
                    formatLabel = 'JSON';
                    break;
                case 'code':
                    clipboardContent = typeof pane.content === 'string' ? pane.content : JSON.stringify(pane.content, null, 2);
                    break;
                case 'doc':
                    if (typeof pane.content === 'string' && pane.content.startsWith('blob:')) {
                        workspaceActions.addNotification('Binary files (like PDFs) cannot be clipped.', 'error');
                        return false;
                    }
                    clipboardContent = String(pane.content);
                    break;
                case 'visual':
                    clipboardContent = typeof pane.content === 'string' ? pane.content : (pane.content?.url || pane.content?.src || '');
                    formatLabel = 'URL';
                    break;
                case 'data':
                    clipboardContent = JSON.stringify(pane.content, null, 2);
                    formatLabel = 'JSON';
                    break;
                default:
                    workspaceActions.addNotification(`Cannot clip pane of type: ${pane.type}`, 'error');
                    return false;
            }

            if (!clipboardContent) {
                workspaceActions.addNotification('Pane content is empty.', 'error');
                return false;
            }

            navigator.clipboard.writeText(clipboardContent).then(() => {
                workspaceActions.addNotification(`Content copied to clipboard as ${formatLabel}`, 'success');
            }).catch(err => {
                workspaceActions.addNotification(`failed to copy: ${err}`, 'error');
            });

            return true;
        } catch (e) {
            workspaceActions.addNotification(`Clipping failed: ${e}`, 'error');
            return false;
        }
    });

    // --- UI Control Handlers Converted ---

    // --- Data Command Handlers ---
    useCommandHandler(COMMAND_NAMES.PLOT, async (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!sourceId) {
            workspaceActions.addNotification('No pane selected for plotting', 'error');
            return false;
        }

        const prompt = payload.action || 'Generate visualization';

        try {
            const { apiClient } = await import('../lib/apiClient');
            const response = await apiClient.plot(sourceId, prompt);

            const newPaneId = `P${Date.now()}`;
            workspaceActions.addPane({
                id: newPaneId,
                type: 'visual',
                title: `Plot: ${sourceId}`,
                content: response.result.url,
                isSticky: false,
                lineage: {
                    parentIds: [sourceId],
                    command: payload.original || `/plot ${sourceId} "${prompt}"`,
                    timestamp: new Date().toISOString()
                }
            });

            workspaceActions.addNotification('Plot generated successfully', 'success');
            return true;
        } catch (error) {
            workspaceActions.addNotification(`Plot failed: ${error}`, 'error');
            return false;
        }
    });

    useCommandHandler(COMMAND_NAMES.RUN, async (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!sourceId) {
            workspaceActions.addNotification('No pane selected for code execution', 'error');
            return false;
        }

        const code = payload.action || '';
        if (!code) {
            workspaceActions.addNotification('No code provided', 'error');
            return false;
        }

        try {
            const { apiClient } = await import('../lib/apiClient');
            const response = await apiClient.run(sourceId, code);

            const newPaneId = `P${Date.now()}`;
            workspaceActions.addPane({
                id: newPaneId,
                type: 'code',
                title: `Run: ${sourceId}`,
                content: response.result.output,
                isSticky: false,
                lineage: {
                    parentIds: [sourceId],
                    command: payload.original || `/run ${sourceId} "${code}"`,
                    timestamp: new Date().toISOString()
                }
            });

            workspaceActions.addNotification('Code executed successfully', 'success');
            return true;
        } catch (error) {
            workspaceActions.addNotification(`Execution failed: ${error}`, 'error');
            return false;
        }
    });

    useCommandHandler(COMMAND_NAMES.DIFF, async (payload) => {
        const paneIds = payload.args;
        if (paneIds.length < 2) {
            workspaceActions.addNotification('Need two pane IDs for diff', 'error');
            return false;
        }

        const [id1, id2] = paneIds.map(id => id.toUpperCase());

        try {
            const { apiClient } = await import('../lib/apiClient');
            const response = await apiClient.diff(id1, id2);

            const newPaneId = `P${Date.now()}`;
            workspaceActions.addPane({
                id: newPaneId,
                type: 'data',
                title: `Diff: ${id1} vs ${id2}`,
                content: response.result,
                isSticky: false,
                lineage: {
                    parentIds: [id1, id2],
                    command: payload.original || `/diff ${id1},${id2}`,
                    timestamp: new Date().toISOString()
                }
            });

            workspaceActions.addNotification('Diff completed', 'success');
            return true;
        } catch (error) {
            workspaceActions.addNotification(`Diff failed: ${error}`, 'error');
            return false;
        }
    });

    useCommandHandler(COMMAND_NAMES.SUMMARIZE, async (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!sourceId) {
            workspaceActions.addNotification('No pane selected for summarization', 'error');
            return false;
        }

        try {
            const { apiClient } = await import('../lib/apiClient');
            const response = await apiClient.summarize(sourceId);

            const newPaneId = `P${Date.now()}`;
            workspaceActions.addPane({
                id: newPaneId,
                type: 'doc',
                title: `Summary: ${sourceId}`,
                content: response.result.summary,
                isSticky: false,
                lineage: {
                    parentIds: [sourceId],
                    command: payload.original || `/summarize ${sourceId}`,
                    timestamp: new Date().toISOString()
                }
            });

            workspaceActions.addNotification('Summary generated', 'success');
            return true;
        } catch (error) {
            workspaceActions.addNotification(`Summarization failed: ${error}`, 'error');
            return false;
        }
    });

    // --- Command Metadata Registration ---

    useEffect(() => {
        workspaceActions.registerCommands([
            {
                name: COMMAND_NAMES.LOAD,
                description: 'Open file picker to load content.',
                parameters: [{ name: 'PaneID', description: 'Target pane ID (optional)', required: false, type: 'paneId' }],
                category: 'system',
                shortcut: 'alt+o',
            },
            {
                name: COMMAND_NAMES.CLIP,
                description: 'Copy pane content (text, chat JSON, or image URL) to clipboard.',
                parameters: [{ name: 'PaneID', description: 'Source pane ID (optional)', required: false, type: 'paneId' }],
                category: 'pane',
                shortcut: 'alt+y',
            },
            {
                name: COMMAND_NAMES.CHAT,
                description: 'Spawn a new chat pane with an initial message.',
                parameters: [
                    { name: '@P1', description: 'Parent pane context (optional)', required: false },
                    { name: 'Message', description: 'Initial message for the chat', required: true }
                ],
                category: 'system',
                shortcut: 'alt+c',
            },
            {
                name: COMMAND_NAMES.CLEAR,
                description: 'Clear all terminal notifications.',
                category: 'system',
                shortcut: 'ctrl+l',
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

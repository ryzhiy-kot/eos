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

import { useEffect } from 'react';
import { useWorkspaceStore, workspaceActions } from '@/store/workspaceStore';
import { useAuthStore } from '@/store/authStore';
import { CommandEntry } from '@/lib/commandRegistry';
import { parseDurationExpression } from '@/lib/terminalUtils';
import { COMMAND_NAMES } from '@/lib/commandBus';
import { useCommandHandler } from '@/hooks/useCommandHandler';
import { extractPaneId } from '@/lib/parser';

export const useRegisterCommands = (onReady?: () => void) => {
    const activeLayout = useWorkspaceStore(state => state.activeLayout);
    const COMMAND_SESSION_ID = 'eos_command_session_v1';

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
        let target = rawTarget?.toUpperCase();
        if (target?.startsWith('@')) target = extractPaneId(target);
        if (target && useWorkspaceStore.getState().panes[target]) {
            workspaceActions.focusPane(target);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.SWAP, (payload) => {
        let sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        let targetId = payload.args[0];
        if (sourceId?.startsWith('@')) sourceId = extractPaneId(sourceId);
        if (targetId?.startsWith('@')) targetId = extractPaneId(targetId);

        if (sourceId && targetId) {
            workspaceActions.swapPanes(sourceId, targetId.toUpperCase());
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.SHELF, (payload) => {
        // Use provided targetId (from > P1), sourceId (from /shelf P1), or fallback to focusedPaneId
        let targetId = payload.context.sourceId || payload.context.focusedPaneId;
        if (targetId?.startsWith('@')) targetId = extractPaneId(targetId);

        if (targetId) {
            workspaceActions.closePane(targetId); // Moves to shelf
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.ARCHIVE, async (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        const workspaceId = useWorkspaceStore.getState().activeWorkspaceId;
        if (!sourceId || !workspaceId) return false;

        const pane = useWorkspaceStore.getState().panes[sourceId];
        if (!pane) return false;

        // Note: pane.title is removed, so we use ID or fetch artifact name if needed
        const confirmed = window.confirm(`Are you sure you want to PERMANENTLY archive pane ${sourceId}? It will be removed from local state and saved to audit logs.`);
        if (confirmed) {
            try {
                const { apiClient } = await import('../lib/apiClient');
                await apiClient.archivePane(workspaceId, pane);
                workspaceActions.removePane(sourceId);
                workspaceActions.addNotification(`Pane ${sourceId} archived and persisted.`, 'success');
                return true;
            } catch (error) {
                workspaceActions.addNotification(`Archiving failed: ${error}`, 'error');
                return false;
            }
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.HIDE, (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (sourceId) {
            workspaceActions.closePane(sourceId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.LS, (payload) => {
        const isOpen = payload.args[0] === 'close' ? false : true;
        workspaceActions.toggleShelfOverlay(isOpen);
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
        const state = useWorkspaceStore.getState();
        const pane = sourceId ? state.panes[sourceId] : null;
        if (pane) {
            workspaceActions.undoArtifact(pane.artifactId);
            return true;
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.REDO, (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        const state = useWorkspaceStore.getState();
        const pane = sourceId ? state.panes[sourceId] : null;
        if (pane) {
            workspaceActions.redoArtifact(pane.artifactId);
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

    const handleHelp = (payload: any) => {
        const isOpen = payload?.args?.[0] === 'close' ? false : true;
        workspaceActions.toggleHelpOverlay(isOpen);
        return true;
    };

    useCommandHandler(COMMAND_NAMES.HELP, handleHelp);
    useCommandHandler(COMMAND_NAMES.QUESTION, () => handleHelp({}));

    useCommandHandler(COMMAND_NAMES.RENAME, async (payload) => {
        const potentialId = payload.args[0]?.toUpperCase();
        const panes = useWorkspaceStore.getState().panes;
        let paneId: string | null = null;
        let newName: string = "";

        if (potentialId && panes[potentialId] && payload.args.length > 1) {
            paneId = potentialId;
            newName = payload.args.slice(1).join(' ');
        } else {
             const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
             if (sourceId && payload.args.length > 0) {
                 paneId = sourceId;
                 newName = payload.args.join(' ');
             }
        }

        if (paneId && newName) {
            const artifactId = panes[paneId].artifactId;
            try {
                const { apiClient } = await import('../lib/apiClient');
                await apiClient.updateArtifact(artifactId, { name: newName });
                workspaceActions.renameArtifact(artifactId, newName);
                return true;
            } catch (e) {
                workspaceActions.addNotification(`Rename failed: ${e}`, 'error');
                return false;
            }
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

    useCommandHandler(COMMAND_NAMES.INIT, async () => {
        if (activeLayout.length === 0) {
            const initArtifactPayload = {
                type: 'chat' as const,
                name: 'System Initialized',
                payload: { messages: [{ role: 'system', content: 'Welcome to eos. System ready.' }] },
                session_id: 'SESSION_INIT'
            };

            try {
                const { apiClient } = await import('../lib/apiClient');
                const created = await apiClient.createArtifact(initArtifactPayload);

                workspaceActions.addArtifact(created);
                workspaceActions.addPane({
                    id: 'P1',
                    artifactId: created.id,
                    type: 'chat',
                    isSticky: true,
                    lineage: { parentIds: [], command: 'init', timestamp: new Date().toISOString() }
                });
                return true;
            } catch (e) {
                console.error('Failed to init:', e);
                return false;
            }
        }
        return false;
    });

    useCommandHandler(COMMAND_NAMES.CHAT, async (payload) => {
        const initialMessage = payload.action || 'Hello';
        const targetId = payload.targetId && /^P\d+$/.test(payload.targetId) ? payload.targetId : undefined;
        const state = useWorkspaceStore.getState();
        const paneId = targetId || workspaceActions.allocateNextPaneId();
        const sessionId = `SESSION_${paneId}`;

        const newArtifactPayload = {
            type: 'chat' as const,
            name: `Chat: ${initialMessage.substring(0, 20)}`,
            payload: { messages: [{ role: 'user', content: initialMessage }] },
            session_id: sessionId
        };

        let createdArtifact;
        try {
            const { apiClient } = await import('../lib/apiClient');
            createdArtifact = await apiClient.createArtifact(newArtifactPayload);
        } catch (e) {
            console.error('Failed to persist CHAT artifact:', e);
            workspaceActions.addNotification('Failed to create chat artifact', 'error');
            return false;
        }

        const artifactId = createdArtifact.id;
        workspaceActions.addArtifact(createdArtifact);

        workspaceActions.addPane({
            id: paneId,
            artifactId: artifactId,
            type: 'chat',
            isSticky: false,
            lineage: {
                parentIds: payload.context.sourceId ? [payload.context.sourceId] : [],
                command: payload.original || '/chat',
                timestamp: new Date().toISOString()
            }
        });

        try {
            const { apiClient } = await import('../lib/apiClient');
            const response = await apiClient.execute({
                type: 'chat',
                session_id: sessionId,
                action: initialMessage
            });

            if (response.success && response.result.output_message) {
                const assistantMsg = response.result.output_message;
                if (assistantMsg.artifacts) {
                    assistantMsg.artifacts.forEach((art: any) => {
                        workspaceActions.addArtifact(art);
                    });
                }
                const currentArtifact = useWorkspaceStore.getState().artifacts[artifactId];
                if (currentArtifact) {
                    workspaceActions.updateArtifactPayload(artifactId, {
                        messages: [...currentArtifact.payload.messages, assistantMsg]
                    });
                }
            }
        } catch (error) {
            workspaceActions.addNotification(`Chat failed: ${error}`, 'error');
        }

        return true;
    });

    useCommandHandler(COMMAND_NAMES.CLIP, (payload) => {
        const targetId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!targetId) {
            workspaceActions.addNotification('No target pane identified for clipping.', 'error');
            return false;
        }

        const state = useWorkspaceStore.getState();
        const pane = state.panes[targetId];
        if (!pane) {
            workspaceActions.addNotification(`Pane ${targetId} not found.`, 'error');
            return false;
        }

        const artifact = state.artifacts[pane.artifactId];
        if (!artifact) {
            workspaceActions.addNotification(`Artifact for pane ${targetId} not found.`, 'error');
            return false;
        }

        let clipboardContent = '';
        let formatLabel = 'Text';

        try {
            switch (artifact.type) {
                case 'chat':
                    // Need name from artifact metadata
                    const name = artifact.metadata?.name || 'Chat';
                    clipboardContent = JSON.stringify({
                        chat_name: name,
                        history: artifact.payload.messages
                    }, null, 2);
                    formatLabel = 'JSON';
                    break;
                case 'code':
                    clipboardContent = typeof artifact.payload === 'string' ? artifact.payload : artifact.payload.source;
                    break;
                case 'doc':
                    if (artifact.payload.format === 'pdf' || artifact.payload.is_url) {
                        workspaceActions.addNotification('External links or PDFs cannot be clipped directly.', 'error');
                        return false;
                    }
                    clipboardContent = String(artifact.payload.value);
                    break;
                case 'visual':
                    clipboardContent = typeof artifact.payload === 'string' ? artifact.payload : (artifact.payload.url || '');
                    formatLabel = 'URL';
                    break;
                case 'data':
                    clipboardContent = JSON.stringify(artifact.payload.data, null, 2);
                    formatLabel = 'JSON';
                    break;
                default:
                    workspaceActions.addNotification(`Cannot clip artifact of type: ${artifact.type}`, 'error');
                    return false;
            }

            if (!clipboardContent) {
                workspaceActions.addNotification('Artifact payload is empty.', 'error');
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
    const handleDataCommand = async (payload: any, commandName: string) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!sourceId) {
            workspaceActions.addNotification(`No pane selected for ${commandName}`, 'error');
            return false;
        }

        const state = useWorkspaceStore.getState();
        const pane = state.panes[sourceId];
        if (!pane) return false;

        const artifactId = pane.artifactId;
        const artifact = state.artifacts[artifactId];
        if (!artifact) return false;

        try {
            const { apiClient } = await import('../lib/apiClient');
            const context_artifacts = {
                [artifactId]: artifact,
                ...(payload.context.contextArtifacts || {})
            };
            const referenced_artifact_ids = Array.from(new Set([
                artifactId,
                ...(payload.context.referencedArtifactIds || [])
            ]));

            const response = await apiClient.execute({
                type: 'command',
                session_id: COMMAND_SESSION_ID,
                command_name: commandName,
                action: payload.action,
                args: payload.args,
                context_artifacts,
                referenced_artifact_ids
            });

            if (response.success) {
                // Register any full artifacts returned in artifacts or new_artifacts
                if (response.result.new_artifacts) {
                    response.result.new_artifacts.forEach((art: any) => {
                        workspaceActions.addArtifact(art);
                        const newPaneId = workspaceActions.allocateNextPaneId();
                        workspaceActions.addPane({
                            id: newPaneId,
                            artifactId: art.id,
                            type: art.type,
                            isSticky: false,
                            lineage: {
                                parentIds: [sourceId],
                                command: payload.original,
                                timestamp: new Date().toISOString()
                            }
                        });
                    });
                }

                if (response.result.output_message?.artifacts) {
                    response.result.output_message.artifacts.forEach((art: any) => {
                        workspaceActions.addArtifact(art);
                    });
                }

                workspaceActions.addNotification(`${commandName} completed`, 'success');
                return true;
            }
            return false;
        } catch (error) {
            workspaceActions.addNotification(`${commandName} failed: ${error}`, 'error');
            return false;
        }
    };

    useCommandHandler(COMMAND_NAMES.PLOT, (payload) => handleDataCommand(payload, 'plot'));
    useCommandHandler(COMMAND_NAMES.RUN, (payload) => handleDataCommand(payload, 'run'));
    useCommandHandler(COMMAND_NAMES.DIFF, (payload) => handleDataCommand(payload, 'diff'));
    useCommandHandler(COMMAND_NAMES.SUMMARIZE, (payload) => handleDataCommand(payload, 'summarize'));

    useCommandHandler(COMMAND_NAMES.OPTIMIZE as any, async (payload) => {
        const sourceId = payload.context.sourceId || payload.context.focusedPaneId;
        if (!sourceId) {
            workspaceActions.addNotification('No pane selected for optimization', 'error');
            return false;
        }

        const state = useWorkspaceStore.getState();
        const pane = state.panes[sourceId];
        if (!pane) return false;

        const artifactId = pane.artifactId;
        const artifact = state.artifacts[artifactId];
        if (!artifact) return false;

        try {
            const { apiClient } = await import('../lib/apiClient');
            const response = await apiClient.execute({
                type: 'command',
                session_id: COMMAND_SESSION_ID,
                command_name: 'optimize',
                action: payload.action,
                args: payload.args,
                context_artifacts: { [artifactId]: artifact },
                referenced_artifact_ids: [artifactId]
            });

            if (response.success && response.result.new_artifacts?.length > 0) {
                const newArt = response.result.new_artifacts[0];
                const activeVersion = state.activeVersions[artifactId] || 'v1';

                // Instead of adding as new artifact, add as GHOST mutation to current artifact
                const ghostMutation = {
                    id: Math.random() * 10000,
                    artifact_id: artifactId,
                    version_id: `v_ghost_${Date.now()}`,
                    parent_id: activeVersion,
                    timestamp: new Date().toISOString(),
                    origin: {
                        type: 'adhoc_command' as const,
                        sessionId: COMMAND_SESSION_ID,
                        prompt: payload.action,
                        triggeringCommand: '/optimize'
                    },
                    change_summary: 'AI Optimization (Preview)',
                    payload: newArt.payload,
                    status: 'ghost' as const
                };

                // Add to store as ghost
                workspaceActions.commitMutation(artifactId, ghostMutation);
                workspaceActions.addNotification('Optimization preview ready (Ghost Layout)', 'info');
                return true;
            }
            return false;
        } catch (error) {
            workspaceActions.addNotification(`Optimization failed: ${error}`, 'error');
            return false;
        }
    });

    useCommandHandler(COMMAND_NAMES.OPEN, (payload) => {
        const artifactId = payload.args[0];

        // If "close" is passed, close the overlay
        if (artifactId === 'close') {
             workspaceActions.toggleArtifactPicker(false);
             return true;
        }

        // If no artifact ID (or "all"), toggle the picker
        if (!artifactId || artifactId === 'all') {
            const mode = artifactId === 'all' ? 'all' : 'session';
            workspaceActions.toggleArtifactPicker(true, mode);
            return true;
        }

        // Otherwise, open the specific artifact
        const state = useWorkspaceStore.getState();
        const artifact = state.artifacts[artifactId];

        if (artifact) {
             // Close overlay first if it was open
             workspaceActions.toggleArtifactPicker(false);

             const paneId = workspaceActions.allocateNextPaneId();
             workspaceActions.addPane({
                id: paneId,
                artifactId: artifact.id,
                type: artifact.type,
                isSticky: true,
                lineage: {
                    parentIds: payload.context.sourceId ? [payload.context.sourceId] : [],
                    command: `/open ${artifactId}`,
                    timestamp: new Date().toISOString()
                }
             });
             return true;
        } else {
            workspaceActions.addNotification(`Artifact ${artifactId} not found`, 'error');
            return false;
        }
    });

    // --- Command Metadata Registration ---

    useEffect(() => {
        workspaceActions.registerCommands([
            {
                name: COMMAND_NAMES.LOAD,
                description: 'Open file picker to load content.',
                parameters: [{ name: '@P1', description: 'Target pane ID (optional)', required: false, type: 'paneId' }],
                category: 'system',
                shortcut: 'alt+o',
            },
            {
                name: COMMAND_NAMES.CLIP,
                description: 'Copy pane content (text, chat JSON, or image URL) to clipboard.',
                parameters: [{ name: '@P1', description: 'Source pane ID (optional)', required: false, type: 'paneId' }],
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
                parameters: [{ name: '@P1', description: 'ID of the pane to focus', required: false, type: 'paneId' }],
                category: 'pane',
                shortcut: 'ctrl+`',
            },
            {
                name: COMMAND_NAMES.SWAP,
                description: 'Swap the positions of two panes.',
                parameters: [{ name: '@P1', description: 'First pane ID', required: true, type: 'paneId' }, { name: '@P2', description: 'Second pane ID', required: true, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.SHELF,
                description: 'Close the mentioned pane and move it to the shelf.',
                parameters: [{ name: '@P1', description: 'ID of the pane to close', required: false, type: 'paneId' }],
                category: 'pane',
                shortcut: 'alt+w',
            },
            {
                name: COMMAND_NAMES.HIDE,
                description: 'Move a pane to the shelf (temporary remove).',
                parameters: [{ name: '@P1', description: 'ID of the pane to hide', required: false, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.ARCHIVE,
                description: 'Permanently archive a pane (remove from shelf).',
                parameters: [{ name: '@P1', description: 'ID of the pane to archive', required: false, type: 'paneId' }],
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
                parameters: [{ name: '@P1', description: 'ID of the pane to restore', required: true, type: 'paneId' }],
                category: 'utility',
            },
            {
                name: COMMAND_NAMES.UNDO,
                description: 'Undo the last change in a pane.',
                parameters: [{ name: '@P1', description: 'ID of the pane to undo', required: false, type: 'paneId' }],
                category: 'pane',
            },
            {
                name: COMMAND_NAMES.REDO,
                description: 'Redo the last undone change.',
                parameters: [{ name: '@P1', description: 'ID of the pane to redo', required: false, type: 'paneId' }],
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
                parameters: [{ name: '@P1', description: 'ID of pane to rename (optional)', required: false, type: 'paneId' }, { name: 'Name', description: 'New title', required: true }],
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
            { name: COMMAND_NAMES.PLOT, description: 'Generate a chart from data. Supports @P1, @file refs.', example: '/plot @P1 "chart type"', category: 'data', shortcut: 'alt+p' },
            { name: COMMAND_NAMES.RUN, description: 'Execute code against pane data. Supports @P1, @file refs.', example: '/run @P1 "code"', category: 'data', shortcut: 'alt+x' },
            { name: COMMAND_NAMES.DIFF, description: 'Compare two panes or a pane and a file.', example: '/diff @P1,@P2 or /diff @P1,@file', category: 'data', shortcut: 'alt+d' },
            { name: COMMAND_NAMES.SUMMARIZE, description: 'Summarize pane content or an attached file.', example: '/summarize @P1 or /summarize @file', category: 'data', shortcut: 'alt+s' },
            { name: 'OPTIMIZE' as any, description: 'Preview an AI-driven optimization of a pane.', example: '/optimize @P1 "prompt"', category: 'data' as any, shortcut: 'alt+z' },
            { name: COMMAND_NAMES.OPEN, description: 'Open an artifact in a new pane, or open the artifact picker.', example: '/open [all | ArtifactID]', category: 'utility', shortcut: 'alt+a' },
        ] as CommandEntry[]);
    }, []); // Static registry, run once
};

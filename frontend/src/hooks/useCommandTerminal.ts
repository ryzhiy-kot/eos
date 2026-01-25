import { useState, useRef, useEffect, useCallback } from 'react';
import { useWorkspaceStore, PaneType, workspaceActions } from '../store/workspaceStore';
import { parseCommand } from '../lib/parser';
import { generatePaneId } from '../lib/terminalUtils';
import { COMMAND_NAMES, commandBus, CommandName } from '../lib/commandBus';
import { useCommandHandler } from './useCommandHandler';
import { apiClient } from '../lib/apiClient';

export const useCommandTerminal = () => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const pendingLoadTargetRef = useRef<string | null>(null);

    const {
        focusedPaneId: activePaneId,
        pendingCommand,
        isOverlayOpen,
        terminalFocusCounter, commandSubmitRequest,
        commands
    } = useWorkspaceStore();

    // Load sessions on mount
    useEffect(() => {
        const loadSessions = async () => {
            try {
                const sessions = await apiClient.listSessions('default_workspace');
                workspaceActions.setChatSessions(sessions);
            } catch (error) {
                console.error('Failed to load sessions:', error);
            }
        };
        loadSessions();
    }, []);

    useCommandHandler(COMMAND_NAMES.LOAD, (payload) => {
        pendingLoadTargetRef.current = payload.args[0]?.toUpperCase() || null;
        fileInputRef.current?.click();
        return true;
    });

    useCommandHandler(COMMAND_NAMES.CLEAR, () => {
        workspaceActions.clearNotification();
        return true;
    });

    const processCommandString = useCallback(async (rawInput: string) => {
        setIsLoading(true);
        try {
            const { type, verb, sourceId, action, targetId } = parseCommand(rawInput, activePaneId);
            const args = action ? action.split(' ') : [];
            const state = useWorkspaceStore.getState();
            const activePane = activePaneId ? state.panes[activePaneId] : null;

            if (type === 'message') {
                // Chat logic: Find or create a chat pane
                let chatPane = activePane && activePane.type === 'chat' ? activePane : null;

                if (!chatPane) {
                    const allPanes = Object.values(state.panes);
                    const chatPanes = allPanes
                        .filter(p => p.type === 'chat')
                        .sort((a, b) => {
                            const timeA = new Date(a.lineage?.timestamp || 0).getTime();
                            const timeB = new Date(b.lineage?.timestamp || 0).getTime();
                            return timeB - timeA;
                        });

                    if (chatPanes.length > 0) {
                        chatPane = chatPanes[0];
                        workspaceActions.focusPane(chatPane.id);
                    }
                }

                if (!chatPane) {
                    const artifactId = `A_CHAT_${Date.now()}`;
                    const paneId = generatePaneId(state.panes);

                    const newArtifact = {
                        id: artifactId,
                        type: 'chat' as PaneType,
                        payload: { messages: [] },
                        session_id: `SESSION_${paneId}`,
                        mutations: []
                    };

                    try { await apiClient.createArtifact(newArtifact); }
                    catch (e) { console.error('Failed to persist auto-chat artifact:', e); }

                    workspaceActions.addArtifact(newArtifact);
                    const newPane = {
                        id: paneId,
                        artifactId: artifactId,
                        type: 'chat' as PaneType,
                        title: `Chat ${paneId}`,
                        isSticky: false,
                        lineage: {
                            parentIds: [],
                            command: 'initial_chat',
                            timestamp: new Date().toISOString()
                        }
                    };
                    workspaceActions.addPane(newPane);
                    chatPane = newPane;
                }

                const artifactId = chatPane.artifactId;
                const artifact = state.artifacts[artifactId];
                if (!artifact) return;

                const paneRefs = rawInput.match(/@P\d+/gi) || [];
                const contextArtifacts: Record<string, any> = {};
                const referencedArtifactIds: string[] = [];
                const optimisticArtifacts: any[] = [];

                paneRefs.forEach(ref => {
                    const id = ref.substring(1).toUpperCase();
                    const p = state.panes[id];
                    if (p) {
                        const r = state.artifacts[p.artifactId];
                        if (r) {
                            contextArtifacts[p.artifactId] = r;
                            referencedArtifactIds.push(p.artifactId);
                            optimisticArtifacts.push(r);
                        }
                    }
                });

                const userMsg = {
                    role: 'user' as const,
                    content: rawInput,
                    referenced_artifact_ids: referencedArtifactIds,
                    artifacts: optimisticArtifacts
                };
                const updatedMessages = [...(artifact.payload.messages || []), userMsg];
                workspaceActions.updateArtifactPayload(artifactId, { messages: updatedMessages });

                try {
                    const sessionId = `SESSION_${chatPane.id}`;
                    const response = await apiClient.execute({
                        type: 'chat',
                        session_id: sessionId,
                        action: rawInput,
                        context_artifacts: contextArtifacts,
                        referenced_artifact_ids: referencedArtifactIds
                    });

                    if (response.success && response.result.output_message) {
                        const assistantMsg = response.result.output_message;

                        // Register any full artifacts returned in artifacts
                        if (assistantMsg.artifacts) {
                            assistantMsg.artifacts.forEach((art: any) => {
                                workspaceActions.addArtifact(art);
                            });
                        }

                        workspaceActions.updateArtifactPayload(artifactId, { messages: [...updatedMessages, assistantMsg] });
                        const sessions = await apiClient.listSessions('default_workspace');
                        workspaceActions.setChatSessions(sessions);
                    }
                } catch (error) {
                    console.error('Chat error:', error);
                    workspaceActions.addNotification('Failed to get chat response', 'error');
                }
            } else if (verb) {
                const cmdName = verb.toLowerCase() as CommandName;
                const executed = await commandBus.dispatch({
                    name: cmdName,
                    args,
                    action: action || undefined,
                    targetId: targetId || undefined,
                    original: rawInput,
                    context: { sourceId: sourceId || undefined, targetId: targetId || undefined, focusedPaneId: activePaneId }
                });

                if (!executed) {
                    workspaceActions.addNotification(`Unknown command: /${verb}`, 'error');
                }
            }
        } catch (error) {
            console.error('Command processing error:', error);
            workspaceActions.addNotification('An error occurred while processing the command.', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [activePaneId]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const targetId = pendingLoadTargetRef.current;
        pendingLoadTargetRef.current = null;

        setIsLoading(true);
        try {
            const state = useWorkspaceStore.getState();
            let type: PaneType = 'doc';
            let payload: any = null;

            if (file.type.startsWith('image/')) {
                type = 'visual';
                payload = { format: 'img', url: URL.createObjectURL(file) };
            } else if (file.type === 'application/pdf') {
                type = 'doc';
                payload = { format: 'pdf', value: URL.createObjectURL(file), is_url: true };
            } else {
                const text = await file.text();
                if (file.type.includes('json') || file.name.endsWith('.json')) {
                    type = 'data';
                    payload = { format: 'json', data: JSON.parse(text) };
                } else if (file.type.includes('javascript') || file.type.includes('python')) {
                    type = 'code';
                    payload = { language: file.type.includes('python') ? 'python' : 'javascript', source: text, filename: file.name };
                } else {
                    const isCodeExtension = file.name.endsWith('.py') || file.name.endsWith('.js') || file.name.endsWith('.ts');
                    type = isCodeExtension ? 'code' : 'doc';
                    if (type === 'code') {
                        payload = { language: file.name.endsWith('.py') ? 'python' : 'typescript', source: text, filename: file.name };
                    } else {
                        payload = { format: 'md', value: text, is_url: false };
                    }
                }
            }

            if (targetId && state.panes[targetId]) {
                const artifactId = state.panes[targetId].artifactId;
                const updatedArtifact = { ...state.artifacts[artifactId], payload };
                workspaceActions.updateArtifactPayload(artifactId, payload, true);
                workspaceActions.renamePane(targetId, file.name);
                workspaceActions.focusPane(targetId);

                // Persist update
                try { await apiClient.createArtifact(updatedArtifact); }
                catch (e) { console.error('Failed to persist artifact update:', e); }
            } else {
                const artifactId = `A_FILE_${Date.now()}`;
                const paneId = generatePaneId(state.panes);
                const newArtifact = {
                    id: artifactId,
                    type,
                    payload,
                    session_id: 'default_session',
                    mutations: []
                };

                // Persist new artifact first
                try { await apiClient.createArtifact(newArtifact); }
                catch (e) { console.error('Failed to persist new artifact:', e); }

                workspaceActions.addArtifact(newArtifact);
                workspaceActions.addPane({
                    id: paneId,
                    artifactId: artifactId,
                    type,
                    title: file.name,
                    isSticky: true,
                    lineage: { parentIds: [], command: `/load ${file.name}`, timestamp: new Date().toISOString() }
                });
            }
        } catch (error) {
            console.error('File load error:', error);
        } finally {
            setIsLoading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        workspaceActions.clearNotification();

        const rawInput = input;
        setInput('');
        await processCommandString(rawInput);
    };

    useEffect(() => {
        if (pendingCommand) {
            setInput(pendingCommand);
            workspaceActions.setPendingCommand(null);
            inputRef.current?.focus();
        }
    }, [pendingCommand, activePaneId]);

    useEffect(() => {
        const handleInteraction = (e: MouseEvent | KeyboardEvent) => {
            if (e instanceof KeyboardEvent && e.key === '`' && e.ctrlKey) {
                e.preventDefault();
                workspaceActions.triggerFocusTerminal();
                return;
            }

            if (e instanceof MouseEvent) {
                requestAnimationFrame(() => {
                    const activeElement = document.activeElement;
                    if (activeElement &&
                        (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') &&
                        activeElement !== inputRef.current) {
                        if (activeElement.closest('.overlay-backdrop, .overlay-window')) {
                            return;
                        }
                    }
                    if (!isOverlayOpen) {
                        inputRef.current?.focus();
                    }
                });
            }
        };

        window.addEventListener('keydown', handleInteraction);
        window.addEventListener('mousedown', handleInteraction);

        return () => {
            window.removeEventListener('keydown', handleInteraction);
            window.removeEventListener('mousedown', handleInteraction);
        };
    }, [isOverlayOpen]);

    useEffect(() => {
        if (!isOverlayOpen && !isLoading) {
            inputRef.current?.focus();
        }
    }, [activePaneId, isOverlayOpen, isLoading]);

    useEffect(() => {
        inputRef.current?.focus();
    }, [terminalFocusCounter]);

    useEffect(() => {
        if (commandSubmitRequest) {
            processCommandString(commandSubmitRequest.command);
        }
    }, [commandSubmitRequest]);

    useEffect(() => {
        const frameId = requestAnimationFrame(() => {
            inputRef.current?.focus();
        });
        return () => cancelAnimationFrame(frameId);
    }, []);

    return {
        input,
        setInput,
        isLoading,
        handleSubmit,
        handleFileSelect,
        inputRef,
        fileInputRef,
        isOverlayOpen,
        activePaneId,
        commands
    };
};

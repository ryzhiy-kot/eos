/**
 * PROJECT: MONAD
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

import { useState, useRef, useEffect, useCallback } from 'react';
import { useWorkspaceStore, workspaceActions } from '@/store/workspaceStore';
import { parseCommand } from '@/lib/parser';
import { generatePaneId } from '@/lib/terminalUtils';
import { COMMAND_NAMES, commandBus, CommandName } from '@/lib/commandBus';
import { useCommandHandler } from '@/hooks/useCommandHandler';
import { apiClient } from '@/lib/apiClient';
import { ChatRole, PaneType } from '@/types/constants'

export const useCommandTerminal = () => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const pendingLoadTargetRef = useRef<string | null>(null);

    const {
        focusedPaneId: activePaneId,
        pendingCommand,
        activeOverlay,
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

    useEffect(() => {
        if (input.includes('@file')) {
            // Trigger if space or enter followed @file, or if it's the only thing
            if (input.endsWith('@file ') || input === '@file') {
                pendingLoadTargetRef.current = 'ATTACH'; // Special marker for attachment
                fileInputRef.current?.click();
                // We'll replace @file with @pending once triggered to avoid loop
                // or just wait for fileSelect to replace it with @A_ID
            }
        }
    }, [input]);

    const processCommandString = useCallback(async (rawInput: string) => {
        setIsLoading(true);
        try {
            const state = useWorkspaceStore.getState();

            // Resolve all @ references in the rawInput
            // Matches @P1, @A_XYZ
            const resourceRefs = rawInput.match(/@(P\d+|A_\w+)/gi) || [];
            const contextArtifacts: Record<string, any> = {};
            const referencedArtifactIds: string[] = [];
            const optimisticArtifacts: any[] = [];

            resourceRefs.forEach(ref => {
                const id = ref.substring(1).toUpperCase();
                let artifactId: string | null = null;

                if (id.startsWith('P')) {
                    const p = state.panes[id];
                    if (p) artifactId = p.artifactId;
                } else if (id.startsWith('A_')) {
                    artifactId = id;
                }

                if (artifactId) {
                    const art = state.artifacts[artifactId];
                    if (art) {
                        contextArtifacts[artifactId] = art;
                        referencedArtifactIds.push(artifactId);
                        optimisticArtifacts.push(art);
                    }
                }
            });

            const { type, verb, sourceId, action, targetId } = parseCommand(rawInput, activePaneId);
            const args = action ? action.split(' ') : [];
            const activePane = activePaneId ? state.panes[activePaneId] : null;

            if (type === 'message') {
                // Chat logic: Find or create a chat pane
                let chatPane = activePane && activePane.type === PaneType.CHAT ? activePane : null;

                if (!chatPane) {
                    const allPanes = Object.values(state.panes);
                    const chatPanes = allPanes
                        .filter(p => p.type === PaneType.CHAT)
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
                        type: PaneType.CHAT,
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
                        type: PaneType.CHAT,
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

                const userMsg = {
                    role: ChatRole.USER,
                    content: rawInput,
                    referenced_artifact_ids: referencedArtifactIds,
                    artifacts: optimisticArtifacts
                };
                const updatedMessages = [...(artifact.payload.messages || []), userMsg];
                workspaceActions.updateArtifactPayload(artifactId, { messages: updatedMessages });

                try {
                    const sessionId = `SESSION_${chatPane.id}`;

                    // Optimistic update for streaming
                    const emptyAssistantMsg = {
                        role: ChatRole.ASSISTANT,
                        content: '',
                        created_at: new Date().toISOString(),
                        artifacts: []
                    };
                    let currentMessages = [...updatedMessages, emptyAssistantMsg];
                    workspaceActions.updateArtifactPayload(artifactId, { messages: currentMessages });

                    const response = await apiClient.executeStream({
                        type: 'chat',
                        session_id: sessionId,
                        action: rawInput,
                        context_artifacts: contextArtifacts,
                        referenced_artifact_ids: referencedArtifactIds,
                        stream: true
                    });

                    let accumulatedText = '';
                    let buffer = '';
                    const reader = response.body?.getReader();
                    const decoder = new TextDecoder();

                    if (reader) {
                        try {
                            while (true) {
                                const { done, value } = await reader.read();
                                if (done) break;

                                const chunk = decoder.decode(value, { stream: true });
                                buffer += chunk;
                                const lines = buffer.split('\n');
                                buffer = lines.pop() || '';

                                for (const line of lines) {
                                    if (line.trim() === '') continue;
                                    if (line.startsWith('data: ')) {
                                        try {
                                            const data = JSON.parse(line.substring(6));

                                            if (data.type === 'text_delta') {
                                                accumulatedText += data.content;
                                                currentMessages = [...currentMessages];
                                                currentMessages[currentMessages.length - 1] = {
                                                    ...currentMessages[currentMessages.length - 1],
                                                    content: accumulatedText
                                                };
                                                workspaceActions.updateArtifactPayload(artifactId, { messages: currentMessages });
                                            } else if (data.type === 'final_message') {
                                                const finalMsg = data.message;
                                                currentMessages = [...currentMessages];
                                                currentMessages[currentMessages.length - 1] = finalMsg;
                                                workspaceActions.updateArtifactPayload(artifactId, { messages: currentMessages });

                                                if (finalMsg.artifacts) {
                                                    finalMsg.artifacts.forEach((art: any) => {
                                                        workspaceActions.addArtifact(art);
                                                    });
                                                }
                                            }
                                        } catch (e) {
                                            console.error('Error parsing SSE', e);
                                        }
                                    }
                                }
                            }
                        } finally {
                            reader.releaseLock();
                        }
                    }

                    const sessions = await apiClient.listSessions('default_workspace');
                    workspaceActions.setChatSessions(sessions);
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
                    context: {
                        sourceId: sourceId || undefined,
                        targetId: targetId || undefined,
                        focusedPaneId: activePaneId,
                        referencedArtifactIds,
                        contextArtifacts
                    }
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
            let type: PaneType = PaneType.DOC;
            let payload: any = null;

            if (file.type.startsWith('image/')) {
                type = PaneType.VISUAL;
                payload = { format: 'img', url: URL.createObjectURL(file) };
            } else if (file.type === 'application/pdf') {
                type = PaneType.DOC;
                payload = { format: 'pdf', value: URL.createObjectURL(file), is_url: true };
            } else {
                const text = await file.text();
                if (file.type.includes('json') || file.name.endsWith('.json')) {
                    type = PaneType.DATA;
                    payload = { format: 'json', data: JSON.parse(text) };
                } else if (file.type.includes('javascript') || file.type.includes('python')) {
                    type = PaneType.CODE;
                    payload = { language: file.type.includes('python') ? 'python' : 'javascript', source: text, filename: file.name };
                } else {
                    const isCodeExtension = file.name.endsWith('.py') || file.name.endsWith('.js') || file.name.endsWith('.ts');
                    type = isCodeExtension ? PaneType.CODE : PaneType.DOC;
                    if (type === PaneType.CODE) {
                        payload = { language: file.name.endsWith('.py') ? 'python' : 'typescript', source: text, filename: file.name };
                    } else {
                        payload = { format: 'md', value: text, is_url: false };
                    }
                }
            }

            if (targetId === 'ATTACH') {
                const artifactId = `A_FILE_${Date.now()}`;
                const newArtifact = {
                    id: artifactId,
                    type,
                    payload,
                    session_id: 'default_session',
                    mutations: [],
                    metadata: { filename: file.name }
                };

                // Persist new artifact first
                try { await apiClient.createArtifact(newArtifact); }
                catch (e) { console.error('Failed to persist attached artifact:', e); }

                workspaceActions.addArtifact(newArtifact);

                // Replace @file in the input with @A_ID
                setInput(prev => prev.replace(/@file\s?/, `@${artifactId} `));
            } else if (targetId && state.panes[targetId]) {
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
                    mutations: [],
                    metadata: { filename: file.name }
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

        // If @file is present and we haven't handled it yet, trigger it
        if (input.includes('@file')) {
            pendingLoadTargetRef.current = 'ATTACH';
            fileInputRef.current?.click();
            return;
        }

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
                    if (!activeOverlay) {
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
    }, [activeOverlay]);

    useEffect(() => {
        if (!activeOverlay && !isLoading) {
            inputRef.current?.focus();
        }
    }, [activePaneId, activeOverlay, isLoading]);

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
        activeOverlay,
        activePaneId,
        commands
    };
};

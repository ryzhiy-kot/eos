import { useState, useRef, useEffect, useCallback } from 'react';
import { useWorkspaceStore, PaneType, workspaceActions } from '../store/workspaceStore';
import { parseCommand } from '../lib/parser';
import { mockExecute } from '../lib/mockBackend';
import { generatePaneId } from '../lib/terminalUtils';
import { commandBus, CommandName, COMMAND_NAMES } from '../lib/commandBus';

export const useCommandTerminal = () => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const {
        focusedPaneId: activePaneId, panes,
        pendingCommand,
        isArchiveOpen, isHelpOpen,
        terminalFocusCounter, commandSubmitRequest,
        commands
    } = useWorkspaceStore();

    const processCommandString = useCallback(async (rawInput: string) => {
        setIsLoading(true);
        try {
            const { type, verb, sourceId, action, targetId } = parseCommand(rawInput, activePaneId);
            const args = action ? action.split(' ') : [];
            const activePane = activePaneId ? panes[activePaneId] : null;

            if (type === 'message') {
                if (activePane && activePane.type === 'chat') {
                    const newContent = [...(activePane.content || []), { role: 'user', content: rawInput }];
                    workspaceActions.updatePaneContent(activePane.id, newContent);

                    setTimeout(() => {
                        const response = { role: 'assistant', content: `Echo: ${rawInput}` };
                        workspaceActions.updatePaneContent(activePane.id, [...newContent, response]);
                    }, 500);
                }
            } else if (verb) {
                // 1. Try to dispatch as an internal command via the Bus
                const cmdName = verb.toLowerCase() as CommandName;
                const executed = await commandBus.dispatch({
                    name: cmdName,
                    args,
                    context: { sourceId: sourceId || undefined, targetId: targetId || undefined, focusedPaneId: activePaneId }
                });

                if (!executed) {
                    // 2. Fallback to mock backend
                    const result = await mockExecute(verb, sourceId || undefined, action || undefined, targetId || undefined);

                    // Determine if we should create a new pane or update existing
                    let finalTargetId = targetId;
                    if (finalTargetId === 'new' || !finalTargetId) {
                        const newId = generatePaneId(panes);
                        workspaceActions.addPane({
                            id: newId,
                            type: result.type,
                            title: result.title,
                            content: result.content,
                            isSticky: false,
                            lineage: {
                                parentIds: sourceId ? [sourceId] : [],
                                command: rawInput,
                                timestamp: new Date().toISOString()
                            }
                        });
                    } else if (panes[finalTargetId]) {
                        workspaceActions.updatePaneContent(finalTargetId, result.content);
                    } else {
                        workspaceActions.addPane({
                            id: finalTargetId,
                            type: result.type,
                            title: result.title,
                            content: result.content,
                            isSticky: false,
                            lineage: {
                                parentIds: sourceId ? [sourceId] : [],
                                command: rawInput,
                                timestamp: new Date().toISOString()
                            }
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Command processing error:', error);
        } finally {
            setIsLoading(false);
        }
    }, [activePaneId, panes]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsLoading(true);
        try {
            const newId = generatePaneId(panes);
            let type: PaneType = 'doc';
            let content: any = '';

            if (file.type.startsWith('image/')) {
                type = 'visual';
                content = URL.createObjectURL(file);
            } else if (file.type === 'application/pdf') {
                type = 'doc';
                content = URL.createObjectURL(file);
            } else {
                // Default to text-based reading for code/data/docs
                content = await file.text();
                if (file.type.includes('json') || file.name.endsWith('.json')) {
                    type = 'data';
                } else if (file.type.includes('javascript') || file.type.includes('python')) {
                    type = 'code';
                } else {
                    type = file.name.endsWith('.py') || file.name.endsWith('.js') || file.name.endsWith('.ts') ? 'code' : 'doc';
                }
            }

            workspaceActions.addPane({
                id: newId,
                type,
                title: file.name,
                content,
                isSticky: true,
                lineage: { parentIds: [], command: `/load ${file.name}`, timestamp: new Date().toISOString() }
            });
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
        const rawInput = input;
        setInput('');
        await processCommandString(rawInput);
    };

    useEffect(() => {
        if (pendingCommand) {
            setInput(pendingCommand);
            commandBus.dispatch({ name: COMMAND_NAMES.UI_PENDING_SET, args: [], context: { focusedPaneId: activePaneId } });
            inputRef.current?.focus();
        }
    }, [pendingCommand, activePaneId]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === '`' && e.ctrlKey) {
                e.preventDefault();
                workspaceActions.triggerFocusTerminal();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    useEffect(() => {
        inputRef.current?.focus();
    }, [terminalFocusCounter]);

    useEffect(() => {
        if (commandSubmitRequest) {
            processCommandString(commandSubmitRequest.command);
        }
    }, [commandSubmitRequest]);

    return {
        input,
        setInput,
        isLoading,
        handleSubmit,
        handleFileSelect,
        inputRef,
        fileInputRef,
        isArchiveOpen,
        isHelpOpen,
        activePaneId,
        commands
    };
};

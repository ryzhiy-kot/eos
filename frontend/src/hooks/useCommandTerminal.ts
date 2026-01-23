import { useState, useRef, useEffect, useCallback } from 'react';
import { useWorkspaceStore, PaneType, workspaceActions } from '../store/workspaceStore';
import { parseCommand } from '../lib/parser';
import { generatePaneId } from '../lib/terminalUtils';
import { COMMAND_NAMES, commandBus, CommandName } from '../lib/commandBus';
import { useCommandHandler } from './useCommandHandler';

export const useCommandTerminal = () => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const pendingLoadTargetRef = useRef<string | null>(null);

    const {
        focusedPaneId: activePaneId, panes,
        pendingCommand,
        isOverlayOpen,
        terminalFocusCounter, commandSubmitRequest,
        commands
    } = useWorkspaceStore();

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
    }, [activePaneId, panes]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const targetId = pendingLoadTargetRef.current;
        pendingLoadTargetRef.current = null; // Clear immediately

        setIsLoading(true);
        try {
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

            if (targetId && panes[targetId]) {
                // Update existing pane
                workspaceActions.updatePaneContent(targetId, content, true);
                // Also update title and type since a new file was loaded
                useWorkspaceStore.setState((state) => ({
                    panes: {
                        ...state.panes,
                        [targetId]: { ...state.panes[targetId], title: file.name, type }
                    }
                }));
                workspaceActions.focusPane(targetId);
            } else {
                // Create new pane
                const newId = generatePaneId(panes);
                workspaceActions.addPane({
                    id: newId,
                    type,
                    title: file.name,
                    content,
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
            // Priority 1: Ctrl+` always triggers focus
            if (e instanceof KeyboardEvent && e.key === '`' && e.ctrlKey) {
                e.preventDefault();
                workspaceActions.triggerFocusTerminal();
                return;
            }

            // Priority 2: Maintain focus on terminal unless an overlay/dialog input is targeted
            if (e instanceof MouseEvent) {
                // Wait for the click to process so we don't block selection or normal browser behavior
                requestAnimationFrame(() => {
                    const activeElement = document.activeElement;

                    // If we clicked something that naturally takes focus (like an input or textarea)
                    // and it's NOT our terminal input, check if it's inside an overlay
                    if (activeElement &&
                        (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') &&
                        activeElement !== inputRef.current) {

                        // If it's in a dialog or overlay, let it keep focus
                        if (activeElement.closest('.overlay-backdrop, .overlay-window')) {
                            return;
                        }
                    }

                    // For all other clicks (workspace background, pane headers, clocks, etc.)
                    // OR if the clicked element was an input NOT in an overlay (which shouldn't happen but just in case)
                    // enforce terminal focus.
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

    // Refocus when active pane changes or command finishes, if no overlay is open
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

    // Initial focus on mount (e.g., after login or refresh) - optimized to avoid magic timers
    useEffect(() => {
        // We use requestAnimationFrame to ensure the focus happens after the browser has finished layout/paint
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

import React, { useState, useRef, useEffect } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { Terminal, Send, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { parseCommand } from '../../lib/parser';
import { mockExecute } from '../../lib/mockBackend';

const CommandTerminal: React.FC = () => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const {
        focusedPaneId, panes,
        addPane, updatePaneContent, setDensity, focusPane, swapPanes, removePane
    } = useWorkspaceStore();

    // Auto-focus logic
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (document.activeElement !== inputRef.current && !e.ctrlKey && !e.altKey && !e.metaKey && e.key.length === 1) {
                inputRef.current?.focus();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    const activePane = focusedPaneId ? panes[focusedPaneId] : null;

    const getPromptStyle = () => {
        if (!activePane) return { text: 'System', color: 'text-neutral-500' };
        switch (activePane.type) {
            case 'chat': return { text: `Chat:${activePane.id}`, color: 'text-blue-500' };
            case 'data': return { text: `Cmd:${activePane.id}`, color: 'text-emerald-500' };
            default: return { text: `Pane:${activePane.id}`, color: 'text-neutral-500' };
        }
    };

    const prompt = getPromptStyle();

    const generatePaneId = () => {
        const numbers = Object.keys(panes).map(id => parseInt(id.replace(/^P/, ''))).filter(n => !isNaN(n));
        const maxId = numbers.length > 0 ? Math.max(...numbers) : 0;
        return `P${maxId + 1}`;
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsLoading(true);
        try {
            const newId = generatePaneId();
            let content: any = '';
            let type: 'doc' | 'data' | 'code' = 'doc';

            if (file.type === 'application/pdf') {
                content = URL.createObjectURL(file);
                type = 'doc';
            } else if (file.name.endsWith('.csv') || file.name.endsWith('.json')) {
                const text = await file.text();
                // Simple parsing demo
                content = file.name.endsWith('.json') ? JSON.parse(text) : [{ raw: text }];
                type = 'data';
            } else {
                content = await file.text();
                type = file.name.endsWith('.py') || file.name.endsWith('.js') || file.name.endsWith('.ts') ? 'code' : 'doc';
            }

            addPane({
                id: newId,
                type,
                title: file.name,
                content,
                isSticky: true,
                lineage: { parentIds: [], command: `/load ${file.name}`, timestamp: new Date().toISOString() }
            });
        } catch (err) {
            console.error("File load error", err);
        } finally {
            setIsLoading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const executeClientCommand = async (verb: string, args: string[], sourceId?: string, targetId?: string) => {
        switch (verb) {
            case 'grid':
                const density = parseInt(args[0]);
                if ([1, 2, 4, 9].includes(density)) {
                    setDensity(density as 1 | 2 | 4 | 9);
                } else {
                    console.warn("Invalid density. Use 1, 2, 4, or 9.");
                }
                return true;
            case 'focus':
                // Usage: /focus P1
                const targetPane = args[0] || (sourceId as string);
                if (targetPane && panes[targetPane]) {
                    focusPane(targetPane);
                }
                return true;
            case 'swap':
                // Usage: /swap P1 P2
                if (sourceId && args[0]) {
                    swapPanes(sourceId, args[0]);
                }
                return true;
            case 'close':
            case 'hide':
                if (sourceId) removePane(sourceId);
                return true;
            case 'load':
                fileInputRef.current?.click();
                return true;
            default:
                return false; // Not a client command
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const rawInput = input;
        setInput('');

        setIsLoading(true);

        try {
            const { type, verb, sourceId, action, targetId } = parseCommand(rawInput, focusedPaneId);
            const args = action ? action.split(' ') : [];

            if (type === 'message') {
                if (activePane && activePane.type === 'chat') {
                    const newContent = [...(Array.isArray(activePane.content) ? activePane.content : []), { role: 'user', content: rawInput }];
                    updatePaneContent(activePane.id, newContent);
                    setTimeout(() => {
                        const response = { role: 'assistant', content: `Echo: ${rawInput}` };
                        updatePaneContent(activePane.id, [...newContent, response]);
                    }, 500);
                }
            } else if (verb) {
                // Try Client Command First
                const isClient = await executeClientCommand(verb, args, sourceId, targetId);

                if (!isClient) {
                    // Fallback to Mock Backend
                    const result = await mockExecute(verb, sourceId, action, targetId);

                    // Handle Result (Create/Update Pane)
                    let finalTargetId = targetId;

                    // Determine if we should create NEW or update EXISTING
                    // Default logic: If no target specified, create NEW unless overwriting check passes?
                    // Let's standardise: always new unless > Pn specified.

                    if (finalTargetId === 'new' || !finalTargetId) {
                        const newId = generatePaneId();
                        addPane({
                            id: newId,
                            type: result.type,
                            title: result.title,
                            content: result.content,
                            isSticky: false,
                            lineage: { parentIds: sourceId ? [sourceId] : [], command: rawInput, timestamp: new Date().toISOString() }
                        });
                    } else if (panes[finalTargetId]) {
                        updatePaneContent(finalTargetId, result.content);
                    } else {
                        // Target doesn't exist, create it
                        addPane({
                            id: finalTargetId,
                            type: result.type,
                            title: result.title,
                            content: result.content,
                            isSticky: false,
                            lineage: { parentIds: sourceId ? [sourceId] : [], command: rawInput, timestamp: new Date().toISOString() }
                        });
                    }
                }
            }
        } catch (error) {
            console.error("Command failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="h-full w-full flex items-center bg-black border border-neutral-800 rounded px-4 focus-within:border-neutral-600 transition-colors">
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                onChange={handleFileSelect}
            />

            <div className={clsx("flex items-center space-x-2 font-mono font-bold mr-4 select-none", prompt.color)}>
                {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Terminal size={16} />}
                <span>[{prompt.text}] &gt;</span>
            </div>

            <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
                className="flex-1 bg-transparent border-none outline-none text-white font-mono placeholder-neutral-700 disabled:opacity-50"
                placeholder={activePane?.type === 'chat' ? "Type a message..." : "Enter command (e.g. /load, /grid 2)"}
                autoFocus
            />

            <button type="submit" disabled={isLoading} className="text-neutral-600 hover:text-white transition-colors disabled:opacity-50">
                <Send size={16} />
            </button>
        </form>
    );
};

export default CommandTerminal;

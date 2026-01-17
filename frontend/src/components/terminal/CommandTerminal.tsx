import React, { useState, useRef, useEffect } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { Terminal, Send, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { parseCommand } from '../../lib/parser';
import { mockExecute } from '../../lib/mockBackend';
import { CommandContext, CommandEntry } from '../../lib/commandRegistry';
import type { PaneType } from '../../store/workspaceStore';

const CommandTerminal: React.FC = () => {
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Updated destructuring inclusive of states to prevent focus stealing
    const {
        focusedPaneId, panes,
        addPane, updatePaneContent, setDensity, focusPane, swapPanes,
        archivePane, restorePane, toggleArchiveOverlay, undoPane, redoPane,
        addClock, addTimer,
        toggleHelpOverlay, pendingCommand, setPendingCommand,
        isArchiveOpen, isHelpOpen, registerCommands
    } = useWorkspaceStore();

    // Auto-focus logic & Pending Command Check
    useEffect(() => {
        if (pendingCommand) {
            setInput(pendingCommand);
            inputRef.current?.focus();
            setPendingCommand(null);
        }

        const handleKeyDown = (e: KeyboardEvent) => {
            // Do not steal focus if an overlay is open
            if (isArchiveOpen || isHelpOpen) return;

            if (document.activeElement !== inputRef.current && !e.ctrlKey && !e.altKey && !e.metaKey && e.key.length === 1) {
                inputRef.current?.focus();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [pendingCommand, setPendingCommand, isArchiveOpen, isHelpOpen]);

    // Register Core Commands
    useEffect(() => {
        registerCommands([
            {
                name: 'load',
                description: 'Load a file (PDF, CSV, JSON) into a new pane.',
                parameters: [{ name: 'file', description: 'File to load', required: false, type: 'file' }],
                category: 'system',
                handler: (): boolean => {
                    fileInputRef.current?.click();
                    return true;
                }
            },
            {
                name: 'grid',
                description: 'Set the number of visible panes.',
                parameters: [{ name: '1|2|4|9', description: 'Number of panes', required: false, type: 'number' }],
                category: 'system',
                handler: (args: string[]) => {
                    const d = parseInt(args[0]);
                    if ([1, 2, 4, 9].includes(d)) {
                        setDensity(d as 1 | 2 | 4 | 9);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'focus',
                description: 'Switch focus to a specific pane.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to focus', required: false, type: 'paneId' }],
                category: 'pane',
                handler: (args: string[], ctx: CommandContext) => {
                    const target = args[0] || ctx.sourceId;
                    if (target && panes[target]) {
                        focusPane(target);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'swap',
                description: 'Swap the positions of two panes.',
                parameters: [{ name: 'P1', description: 'First pane ID', required: true, type: 'paneId' }, { name: 'P2', description: 'Second pane ID', required: true, type: 'paneId' }],
                category: 'pane',
                handler: (args: string[], ctx: CommandContext) => {
                    if (ctx.sourceId && args[0]) {
                        swapPanes(ctx.sourceId, args[0]);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'close',
                description: 'Archive a pane (alias for /hide).',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to close', required: false, type: 'paneId' }],
                category: 'pane',
                handler: (_: string[], ctx: CommandContext) => {
                    if (ctx.sourceId) {
                        archivePane(ctx.sourceId);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'hide',
                description: 'Archive a pane (alias for /close).',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to hide', required: false, type: 'paneId' }],
                category: 'pane',
                handler: (_: string[], ctx: CommandContext) => {
                    if (ctx.sourceId) {
                        archivePane(ctx.sourceId);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'ls',
                description: 'Open the Archive Gallery (The Shelf).',
                category: 'utility',
                handler: (): boolean => {
                    toggleArchiveOverlay(true);
                    return true;
                }
            },
            {
                name: 'show',
                description: 'Restore a pane from the archive.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to restore', required: true, type: 'paneId' }],
                category: 'utility',
                handler: (args: string[], ctx: CommandContext) => {
                    const rid = args[0] || ctx.sourceId;
                    if (rid) {
                        restorePane(rid);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'undo',
                description: 'Undo the last change in a pane.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to undo', required: false, type: 'paneId' }],
                category: 'pane',
                handler: (_: string[], ctx: CommandContext) => {
                    if (ctx.sourceId) {
                        undoPane(ctx.sourceId);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'redo',
                description: 'Redo the last undone change.',
                parameters: [{ name: 'PaneID', description: 'ID of the pane to redo', required: false, type: 'paneId' }],
                category: 'pane',
                handler: (_: string[], ctx: CommandContext) => {
                    if (ctx.sourceId) {
                        redoPane(ctx.sourceId);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'clock',
                description: 'Add a world clock to the header.',
                parameters: [{ name: 'City', description: 'City name', required: true }, { name: 'Zone', description: 'Timezone identifier', required: true }],
                category: 'utility',
                handler: (args: string[]) => {
                    if (args.length >= 2) {
                        addClock(args[0], args[1]);
                        return true;
                    }
                    return false;
                }
            },
            {
                name: 'timer',
                description: 'Start a countdown timer.',
                parameters: [{ name: 'Sec', description: 'Duration in seconds', required: true, type: 'number' }, { name: 'Label', description: 'Timer label', required: false }],
                category: 'utility',
                handler: (args: string[]) => {
                    if (args.length > 0) {
                        const { seconds, labelStartIdx } = parseDurationExpression(args);
                        const label = args.slice(labelStartIdx).join(' ') || 'Timer';
                        if (seconds > 0) {
                            addTimer(label, seconds);
                            return true;
                        }
                    }
                    return false;
                }
            },
            {
                name: 'help',
                description: 'Show command help.',
                category: 'utility',
                handler: (): boolean => {
                    toggleHelpOverlay(true);
                    return true;
                }
            },
            {
                name: '?',
                description: 'Show command help (alias for /help).',
                category: 'utility',
                handler: (): boolean => {
                    toggleHelpOverlay(true);
                    return true;
                }
            },
            // Data/Mock commands (no local handler, will fail isClient and fall back to mockExecute)
            { name: 'plot', description: 'Generate a chart from data.', example: '/plot [P1] "prompt"', category: 'data' },
            { name: 'run', description: 'Execute code against pane data.', example: '/run [P1] "code"', category: 'data' },
            { name: 'diff', description: 'Compare two panes.', example: '/diff [P1],[P2]', category: 'data' },
        ] as CommandEntry[]);
    }, [registerCommands, panes, setDensity, focusPane, swapPanes, archivePane, restorePane, toggleArchiveOverlay, toggleHelpOverlay, undoPane, redoPane, addClock, addTimer]);

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
            let type: PaneType = "empty";
            if (file.type === 'application/pdf') {
                content = URL.createObjectURL(file);
                type = 'doc';
            } else if (file.type.startsWith('image/')) {
                content = URL.createObjectURL(file);
                type = 'visual';
            } else if (file.name.endsWith('.csv') || file.name.endsWith('.json')) {
                const text = await file.text();
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

    // Timer parsing helper
    const parseDurationExpression = (inputArgs: string[]): { seconds: number, labelStartIdx: number } => {
        let totalSeconds = 0;
        let ptr = 0;
        let hasTime = false;

        while (ptr < inputArgs.length) {
            const arg = inputArgs[ptr].toLowerCase();

            // Check for "20m", "50s" format
            const combinedMatch = arg.match(/^(\d+)([ms])$/);
            if (combinedMatch) {
                const val = parseInt(combinedMatch[1]);
                const unit = combinedMatch[2];
                totalSeconds += unit === 'm' ? val * 60 : val;
                hasTime = true;
                ptr++;
                continue;
            }

            // Check for pure number
            if (/^\d+$/.test(arg)) {
                const val = parseInt(arg);
                // Look ahead for unit
                if (ptr + 1 < inputArgs.length) {
                    const next = inputArgs[ptr + 1].toLowerCase();
                    if (['m', 's', 'min', 'sec', 'mins', 'secs', 'minute', 'minutes'].includes(next)) {
                        if (next.startsWith('s')) totalSeconds += val;
                        else totalSeconds += val * 60;
                        hasTime = true;
                        ptr += 2;
                        continue;
                    }
                }

                // No explicit unit following
                if (!hasTime) {
                    // First number encountered, default to minutes as per requirement
                    totalSeconds += val * 60;
                    hasTime = true;
                    ptr++;
                } else {
                    // Subsequent number, assume seconds (e.g., "20 minutes 50")
                    totalSeconds += val;
                    ptr++;
                }
                continue;
            }

            // Hit something else (label starts)
            break;
        }

        return { seconds: totalSeconds, labelStartIdx: ptr };
    };

    const executeClientCommand = async (verb: string, args: string[], sourceId?: string, targetId?: string) => {
        const cmdName = verb.toLowerCase();
        const entry = useWorkspaceStore.getState().commands.find(c => c.name === cmdName);

        if (entry && entry.handler) {
            return await entry.handler(args, { sourceId, targetId, focusedPaneId });
        }

        return false;
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
                const isClient = await executeClientCommand(verb, args, sourceId, targetId);

                if (!isClient) {
                    const result = await mockExecute(verb, sourceId, action, targetId);

                    let finalTargetId = targetId;

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
                placeholder={activePane?.type === 'chat' ? "Type a message..." : "Enter command, e.g. /help, /load, /ls"}
                autoFocus
            />

            <button type="submit" disabled={isLoading} className="text-neutral-600 hover:text-white transition-colors disabled:opacity-50">
                <Send size={16} />
            </button>
        </form>
    );
};

export default CommandTerminal;

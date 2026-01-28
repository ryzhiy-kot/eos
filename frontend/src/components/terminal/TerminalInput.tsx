import React, { useMemo, useRef } from 'react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { X } from 'lucide-react';

interface TerminalInputProps {
    input: string;
    setInput: (val: string | ((prev: string) => string)) => void;
    isLoading: boolean;
    inputRef: React.RefObject<HTMLInputElement | null>;
    fileInputRef: React.RefObject<HTMLInputElement | null>;
    onSubmit: (e: React.FormEvent) => void;
    onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
    activePaneId: string | null;
    paneType?: string;
}

const TerminalInput: React.FC<TerminalInputProps> = ({
    input, setInput,
    isLoading,
    inputRef, fileInputRef,
    onSubmit,
    onFileSelect,
    activePaneId,
    paneType
}) => {
    const { panes, artifacts } = useWorkspaceStore();

    // Derive attachments from input text
    const attachments = useMemo(() => {
        const refs = input.match(/@(P\d+|A_\w+)/gi) || [];
        return Array.from(new Set(refs)).map(ref => {
            const id = ref.substring(1).toUpperCase();
            let label = ref;
            let type: 'pane' | 'artifact' = 'artifact';

            if (id.startsWith('P')) {
                type = 'pane';
                const p = panes[id];
                label = p ? `${id}: ${p.title}` : id;
            } else if (id.startsWith('A_')) {
                const art = artifacts[id];
                label = art?.metadata?.filename || art?.id || id;
            }

            return { ref, label, type };
        });
    }, [input, panes, artifacts]);

    const handleRemoveAttachment = (ref: string) => {
        setInput(prev => {
            const regex = new RegExp(`${ref}\\s?`, 'gi');
            return prev.replace(regex, '').trimStart();
        });
    };

    // --- Syntax Highlighting Logic ---
    const highlightedInput = useMemo(() => {
        if (!input) return null;

        const tokens = input.split(/(\s+)/);
        return tokens.map((token, i) => {
            if (token.startsWith('/')) {
                return (
                    <span key={i} className="text-primary-light dark:text-primary font-bold">
                        {token}
                    </span>
                );
            }
            if (token.startsWith('@')) {
                return (
                    <span key={i} className="text-purple-600 dark:text-purple-400 font-medium">
                        {token}
                    </span>
                );
            }
            if (token.startsWith('>')) {
                return (
                    <span key={i} className="text-orange-600 dark:text-orange-400 font-bold px-1">
                        {token}
                    </span>
                );
            }
            return <span key={i}>{token}</span>;
        });
    }, [input]);

    // Mirror scrolling to the highlighter div
    const highlighterRef = useRef<HTMLDivElement>(null);
    const scrollSync = () => {
        if (highlighterRef.current && inputRef.current) {
            highlighterRef.current.scrollLeft = inputRef.current.scrollLeft;
        }
    };

    return (
        <div className="flex-1 flex flex-col gap-1">
            {/* Attachment Chips Overlay */}
            {attachments.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-1 animate-in fade-in slide-in-from-bottom-1 duration-200">
                    {attachments.map((at, i) => (
                        <div
                            key={`${at.ref}-${i}`}
                            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-200/50 dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 text-[10px] font-medium text-slate-600 dark:text-slate-400 group hover:border-primary/50 transition-colors"
                        >
                            <span className="opacity-70">{at.type === 'pane' ? 'Pane' : 'File'}:</span>
                            <span className="max-w-[120px] truncate">{at.label}</span>
                            <button
                                type="button"
                                onClick={() => handleRemoveAttachment(at.ref)}
                                className="p-0.5 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-full transition-colors"
                            >
                                <X size={10} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <div className="flex items-center gap-3">
                {/* Context Breadcrumb */}
                <span className="bg-primary/20 text-primary px-2 py-1 rounded text-xs font-bold border border-primary/50 whitespace-nowrap">
                    [{activePaneId || 'SYS'}]
                </span>
                <span className="text-slate-400 select-none text-lg">&gt;</span>

                <form onSubmit={onSubmit} className="flex-1 relative flex items-center overflow-hidden">
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        onChange={onFileSelect}
                    />

                    {/* Syntax Highlighting Overlay (Mirrors input text with color) */}
                    <div
                        ref={highlighterRef}
                        aria-hidden="true"
                        className="absolute inset-0 pointer-events-none whitespace-pre text-lg font-mono flex items-center overflow-hidden"
                        style={{ padding: '0px' }}
                    >
                        {/* 
                            This div renders invisible characters to maintain spacing 
                            exactly like the native input. 
                        */}
                        <span className="text-transparent">
                            {highlightedInput}
                        </span>
                    </div>

                    {/* Visible Highlighted Layer */}
                    <div
                        className="absolute inset-0 pointer-events-none whitespace-pre text-lg font-mono flex items-center overflow-hidden"
                        style={{ padding: '0px' }}
                    >
                        {highlightedInput}
                    </div>

                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onScroll={scrollSync}
                        disabled={isLoading}
                        className="w-full bg-transparent border-none outline-none ring-0 p-0 text-lg focus:ring-0 text-transparent caret-slate-700 dark:caret-slate-200 placeholder-slate-500 font-mono relative z-10"
                        placeholder={paneType === 'chat' ? "Type a message..." : "Enter command..."}
                        autoFocus
                    />
                </form>
            </div>
        </div>
    );
};

export default TerminalInput;

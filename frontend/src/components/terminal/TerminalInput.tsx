import React from 'react';

interface TerminalInputProps {
    input: string;
    setInput: (val: string) => void;
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
    return (
        <div className="flex-1 flex items-center gap-3">
            {/* Context Breadcrumb */}
            <span className="bg-primary/20 text-primary px-2 py-1 rounded text-xs font-bold border border-primary/50 whitespace-nowrap">
                [{activePaneId || 'SYS'}]
            </span>
            <span className="text-slate-400 select-none text-lg">&gt;</span>

            <form onSubmit={onSubmit} className="flex-1 flex items-center">
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    onChange={onFileSelect}
                />

                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={isLoading}
                    className="w-full bg-transparent border-none outline-none ring-0 p-0 text-lg focus:ring-0 text-slate-700 dark:text-slate-200 placeholder-slate-500 font-mono"
                    placeholder={paneType === 'chat' ? "Type a message..." : "Enter command..."}
                    autoFocus
                />
            </form>
        </div>
    );
};

export default TerminalInput;

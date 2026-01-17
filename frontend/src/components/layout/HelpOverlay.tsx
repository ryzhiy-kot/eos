import React, { useState, useEffect } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { Search, Terminal, ArrowRight } from 'lucide-react';
import OverlayWindow from './OverlayWindow';
import { formatCommandUsage } from '../../lib/commandRegistry';
import clsx from 'clsx';

const HelpOverlay: React.FC = () => {
    const { isHelpOpen, toggleHelpOverlay, setPendingCommand, commands } = useWorkspaceStore();
    const [search, setSearch] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);

    const filteredCommands = commands.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.description.toLowerCase().includes(search.toLowerCase())
    );

    // Reset selection when search changes or overlay opens
    useEffect(() => {
        setSelectedIndex(0);
    }, [search, isHelpOpen]);

    const handleSelect = (name: string) => {
        setPendingCommand(`/${name} `);
        toggleHelpOverlay(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev + 1) % filteredCommands.length);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (filteredCommands.length > 0) {
                handleSelect(filteredCommands[selectedIndex].name);
            } else {
                toggleHelpOverlay(false);
            }
        }
    };

    return (
        <OverlayWindow
            title="Command Center (Help)"
            subtitle="Registry-Driven"
            isOpen={isHelpOpen}
            onClose={() => toggleHelpOverlay(false)}
        >
            <div className="flex flex-col h-full">
                {/* Search */}
                <div className="mb-8 w-full max-w-2xl mx-auto relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-blue-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search commands..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-neutral-900 border border-neutral-800 rounded-full py-3 pl-12 pr-4 text-white font-mono focus:border-blue-500 outline-none transition-colors"
                        autoFocus
                    />
                </div>

                {/* Command Grid */}
                <div className="flex-1 overflow-y-auto">
                    <div className="grid grid-cols-1 gap-2">
                        {filteredCommands.map((c, i) => (
                            <div
                                key={c.name}
                                onClick={() => handleSelect(c.name)}
                                className={clsx(
                                    "group flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer",
                                    i === selectedIndex
                                        ? "border-blue-500 bg-neutral-900"
                                        : "border-neutral-800 hover:border-neutral-600 hover:bg-neutral-900/50"
                                )}
                            >
                                <div className="flex items-center space-x-4">
                                    <div className={clsx(
                                        "p-2 rounded transition-colors",
                                        i === selectedIndex ? "bg-blue-500/10 text-blue-400" : "bg-neutral-800 text-neutral-400"
                                    )}>
                                        <Terminal size={20} />
                                    </div>
                                    <div>
                                        <div className={clsx(
                                            "font-mono font-bold text-lg transition-colors",
                                            i === selectedIndex ? "text-blue-400" : "text-white"
                                        )}>
                                            {formatCommandUsage(c)}
                                        </div>
                                        <div className="text-neutral-500 text-sm">
                                            {c.description}
                                        </div>
                                    </div>
                                </div>
                                <ArrowRight className={clsx(
                                    "transition-colors",
                                    i === selectedIndex ? "text-white" : "text-neutral-700 group-hover:text-neutral-500"
                                )} />
                            </div>
                        ))}

                        {commands.length === 0 && (
                            <div className="text-center text-neutral-500 py-12">
                                Registry is empty. Commands are being initialized...
                            </div>
                        )}

                        {commands.length > 0 && filteredCommands.length === 0 && (
                            <div className="text-center text-neutral-500 py-12">
                                No commands found matching "{search}"
                            </div>
                        )}
                    </div>
                </div>

                <div className="mt-4 text-center text-neutral-600 font-mono text-xs opacity-75">
                    Use ↑↓ to navigate • Press [Enter] to select highlighted or close
                </div>
            </div>
        </OverlayWindow>
    );
};

export default HelpOverlay;

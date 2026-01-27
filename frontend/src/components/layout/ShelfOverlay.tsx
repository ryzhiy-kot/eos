import React, { useState, useEffect } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { Search, MonitorPlay } from 'lucide-react';
import clsx from 'clsx';
import ContentFactory from '../panes/ContentFactory';
import OverlayWindow from './OverlayWindow';
import { commandBus, COMMAND_NAMES } from '../../lib/commandBus';

const ShelfOverlay: React.FC = () => {
    const { archive, panes, isShelfOpen: isShelfOpen, focusedPaneId } = useWorkspaceStore();
    const [search, setSearch] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);

    const filteredIds = archive.filter(id => {
        const pane = panes[id];
        if (!pane) return false;
        const query = search.toLowerCase();
        return pane.title.toLowerCase().includes(query) || pane.id.toLowerCase().includes(query);
    });

    // Reset selection when search changes or overlay opens
    useEffect(() => {
        setSelectedIndex(0);
    }, [search, isShelfOpen]);

    const handleSelect = (id: string) => {
        commandBus.dispatch({
            name: COMMAND_NAMES.SHOW,
            args: [id],
            context: { sourceId: id, focusedPaneId }
        });
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        const cols = 4; // Max grid columns logic
        const len = filteredIds.length;

        if (len === 0) return;

        if (e.key === 'ArrowRight') {
            e.preventDefault();
            setSelectedIndex(prev => (prev + 1) % len);
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            setSelectedIndex(prev => (prev - 1 + len) % len);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev + cols < len ? prev + cols : prev % cols));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev - cols >= 0 ? prev - cols : (Math.floor((len - 1) / cols) * cols) + (prev % cols)));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            handleSelect(filteredIds[selectedIndex]);
        }
    };

    return (
        <OverlayWindow
            title="The Shelf"
            subtitle={`${archive.length} Items`}
            isOpen={isShelfOpen}
            onClose={() => commandBus.dispatch({ name: COMMAND_NAMES.LS, args: ['close'], context: { focusedPaneId } })}
            maxWidth="max-w-none"
        >
            <div className="flex flex-col h-full">
                {/* Search */}
                <div className="mb-8 w-full max-w-2xl mx-auto relative group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-blue-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="Filter shelf..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-neutral-900 border border-neutral-800 rounded-full py-3 pl-12 pr-4 text-white font-mono focus:border-blue-500 outline-none transition-colors"
                        autoFocus
                    />
                </div>

                {/* Grid */}
                <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-8">
                    {filteredIds.map((id, index) => {
                        const pane = panes[id];
                        const isSelected = index === selectedIndex;
                        return (
                            <div
                                key={id}
                                onClick={() => handleSelect(id)}
                                className={clsx(
                                    "group bg-neutral-900 border rounded-lg overflow-hidden cursor-pointer transition-all flex flex-col h-64",
                                    isSelected
                                        ? "border-blue-500 scale-[1.02] ring-2 ring-blue-500/50 shadow-lg shadow-blue-500/20"
                                        : "border-neutral-800 hover:border-neutral-600 hover:scale-[1.02]"
                                )}
                            >
                                <div className={clsx(
                                    "p-2 border-b flex justify-between items-center transition-colors",
                                    isSelected ? "bg-blue-600/20 border-blue-500/50" : "bg-neutral-950 border-neutral-800"
                                )}>
                                    <span className={clsx(
                                        "font-bold font-mono text-xs",
                                        isSelected ? "text-blue-300" : (pane.type === 'chat' ? 'text-blue-400' : 'text-emerald-400')
                                    )}>
                                        [{pane.type.toUpperCase()}: {pane.id}]
                                    </span>
                                    <span className={clsx(
                                        "text-xs truncate max-w-[150px]",
                                        isSelected ? "text-white" : "text-neutral-500"
                                    )}>{pane.title}</span>
                                </div>
                                <div className={clsx(
                                    "flex-1 overflow-hidden relative transition-opacity bg-neutral-950/50",
                                    isSelected ? "opacity-100" : "opacity-50 group-hover:opacity-100"
                                )}>
                                    {/* Mini Preview */}
                                    <div className="transform scale-50 origin-top-left w-[200%] h-[200%] pointer-events-none p-4">
                                        <ContentFactory pane={pane} />
                                    </div>

                                    {/* Hover Overlay */}
                                    <div className={clsx(
                                        "absolute inset-0 flex items-center justify-center transition-opacity bg-black/40",
                                        isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                                    )}>
                                        <MonitorPlay size={48} className={clsx(
                                            "transition-transform",
                                            isSelected ? "text-blue-400 scale-110" : "text-white"
                                        )} />
                                    </div>
                                </div>
                            </div>
                        )
                    })}

                    {filteredIds.length === 0 && (
                        <div className="col-span-full flex flex-col items-center justify-center text-neutral-600 py-20">
                            <span className="text-4xl mb-4 text-neutral-700">🕸️</span>
                            <span className="font-mono text-sm">No items found in the archive.</span>
                        </div>
                    )}
                </div>

                {filteredIds.length > 0 && (
                    <div className="mt-4 pb-4 text-center text-neutral-600 font-mono text-xs opacity-75 border-t border-neutral-800/50 pt-4">
                        Use ↑↓←→ to navigate • Press [Enter] to restore selected item
                    </div>
                )}
            </div>
        </OverlayWindow>
    );
};

export default ShelfOverlay;

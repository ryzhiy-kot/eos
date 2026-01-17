import React, { useState } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { X, Search, MonitorPlay } from 'lucide-react';
import clsx from 'clsx';
import ContentFactory from '../panes/ContentFactory';

const ArchiveOverlay: React.FC = () => {
    const { archive, panes, toggleArchiveOverlay, restorePane, isArchiveOpen } = useWorkspaceStore();
    const [search, setSearch] = useState('');

    if (!isArchiveOpen) return null;

    const filteredIds = archive.filter(id => {
        const pane = panes[id];
        if (!pane) return false;
        const query = search.toLowerCase();
        return pane.title.toLowerCase().includes(query) || pane.id.toLowerCase().includes(query);
    });

    return (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col p-8 animate-in fade-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between mb-8 border-b border-neutral-800 pb-4">
                <div className="flex items-center space-x-4">
                    <h2 className="text-2xl font-mono font-bold text-white">THE SHELF (ARCHIVE)</h2>
                    <span className="bg-neutral-800 text-neutral-400 px-2 py-1 rounded text-xs font-mono">{archive.length} Items</span>
                </div>
                <button onClick={() => toggleArchiveOverlay(false)} className="text-neutral-500 hover:text-white transition-colors">
                    <X size={32} />
                </button>
            </div>

            {/* Search */}
            <div className="mb-8 w-full max-w-2xl mx-auto relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-blue-500 transition-colors" />
                <input
                    type="text"
                    placeholder="Filter archive..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-neutral-900 border border-neutral-800 rounded-full py-3 pl-12 pr-4 text-white font-mono focus:border-blue-500 outline-none transition-colors"
                    autoFocus
                />
            </div>

            {/* Grid */}
            <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredIds.map(id => {
                    const pane = panes[id];
                    return (
                        <div
                            key={id}
                            onClick={() => restorePane(id)}
                            className="group bg-neutral-900 border border-neutral-800 hover:border-blue-500 rounded-lg overflow-hidden cursor-pointer transition-all hover:scale-[1.02] flex flex-col h-64"
                        >
                            <div className="bg-neutral-950 p-2 border-b border-neutral-800 flex justify-between items-center">
                                <span className={clsx("font-bold font-mono text-xs", pane.type === 'chat' ? 'text-blue-400' : 'text-emerald-400')}>
                                    [{pane.type.toUpperCase()}: {pane.id}]
                                </span>
                                <span className="text-neutral-500 text-xs truncate max-w-[150px]">{pane.title}</span>
                            </div>
                            <div className="flex-1 overflow-hidden relative opacity-50 group-hover:opacity-100 transition-opacity bg-neutral-950/50">
                                {/* Mini Preview - scaled down potentially, or just mocked representation */}
                                <div className="transform scale-50 origin-top-left w-[200%] h-[200%] pointer-events-none p-4">
                                    <ContentFactory pane={pane} />
                                </div>

                                {/* Hover Overlay */}
                                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                                    <MonitorPlay size={48} className="text-white drop-shadow-lg" />
                                </div>
                            </div>
                        </div>
                    )
                })}

                {filteredIds.length === 0 && (
                    <div className="col-span-full flex flex-col items-center justify-center text-neutral-600">
                        <span className="text-4xl mb-4">🕸️</span>
                        <span>No archived items found.</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ArchiveOverlay;

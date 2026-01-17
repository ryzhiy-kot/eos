import React from 'react';
import { useWorkspaceStore, Pane } from '../../store/workspaceStore';
import { X, Maximize2, MoreHorizontal } from 'lucide-react';
import clsx from 'clsx';
import ContentFactory from './ContentFactory';

interface PaneFrameProps {
    pane: Pane;
}

const PaneFrame: React.FC<PaneFrameProps> = ({ pane }) => {
    const { focusedPaneId, focusPane, removePane } = useWorkspaceStore();
    const isFocused = focusedPaneId === pane.id;

    const handleFocus = () => {
        if (!isFocused) focusPane(pane.id);
    };

    return (
        <div
            onClick={handleFocus}
            className={clsx(
                "flex flex-col h-full w-full bg-neutral-900 border transition-colors duration-150 overflow-hidden",
                isFocused ? "border-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.2)]" : "border-neutral-800 hover:border-neutral-700"
            )}
        >
            {/* Pane Header */}
            <div className={clsx(
                "h-8 flex items-center justify-between px-3 text-xs font-mono select-none uppercase tracking-wide",
                isFocused ? "bg-blue-900/20 text-blue-400" : "bg-neutral-900 text-neutral-500"
            )}>
                <div className="flex items-center space-x-2">
                    <span className={clsx("font-bold", pane.isSticky && "text-yellow-500")}>
                        [{pane.type.toUpperCase()}: {pane.id}]
                    </span>
                    <span>{pane.title}</span>
                    {isFocused && <span className="animate-pulse">_</span>}
                </div>

                <div className="flex items-center space-x-2 opacity-50 hover:opacity-100 transition-opacity">
                    <button className="hover:text-white"><Maximize2 size={12} /></button>
                    <button className="hover:text-white"><MoreHorizontal size={12} /></button>
                    {!pane.isSticky && (
                        <button onClick={(e) => { e.stopPropagation(); removePane(pane.id); }} className="hover:text-red-500">
                            <X size={12} />
                        </button>
                    )}
                </div>
            </div>

            {/* Pane Content */}
            <div className="flex-1 overflow-hidden relative">
                <ContentFactory pane={pane} />
            </div>
        </div>
    );
};

export default PaneFrame;

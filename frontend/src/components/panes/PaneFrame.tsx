import React from 'react';
import { useWorkspaceStore, Pane } from '../../store/workspaceStore';
import { X, Maximize2 } from 'lucide-react';
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
                "pane-frame group",
                isFocused && "active"
            )}
        >
            {/* Corner Accents (Top-Left, Bottom-Right) */}
            {isFocused && (
                <>
                    <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-accent-main" />
                    <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-accent-main" />
                </>
            )}

            {/* Pane Header */}
            <div className={clsx(
                "pane-header",
                isFocused && "active"
            )}
            >
                {/* ... content remains same ... */}
                <div className="flex items-center space-x-2">
                    <span className={clsx("font-bold", pane.isSticky ? "text-accent-secondary" : "opacity-70")}>
                        [{pane.type.toUpperCase()}:{pane.id}]
                    </span>
                    <span className="truncate max-w-[150px]">{pane.title}</span>
                </div>

                <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="hover:text-white p-1 hover:bg-white/5 rounded"><Maximize2 size={12} /></button>
                    {!pane.isSticky && (
                        <button
                            onClick={(e) => { e.stopPropagation(); removePane(pane.id); }}
                            className="hover:text-red-500 p-1 hover:bg-white/5 rounded"
                        >
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

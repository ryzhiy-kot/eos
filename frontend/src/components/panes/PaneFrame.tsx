import React from 'react';
import { useWorkspaceStore, Pane } from '../../store/workspaceStore';
import { X, Maximize2 } from 'lucide-react';
import clsx from 'clsx';
import ContentFactory from './ContentFactory';
import { commandBus, COMMAND_NAMES } from '../../lib/commandBus';

interface PaneFrameProps {
    pane: Pane;
}

const PaneFrame: React.FC<PaneFrameProps> = ({ pane }) => {
    const { focusedPaneId } = useWorkspaceStore();
    const isFocused = focusedPaneId === pane.id;

    const handleFocus = () => {
        if (!isFocused) {
            commandBus.dispatch({
                name: COMMAND_NAMES.FOCUS,
                args: [],
                context: { sourceId: pane.id, focusedPaneId }
            });
        }
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
                <div className="flex items-center gap-2">
                    <span className="font-bold text-accent-secondary">
                        [{pane.id}]
                    </span>
                    <span className="font-bold text-slate-700 dark:text-slate-200">
                        [{pane.type.charAt(0).toUpperCase() + pane.type.slice(1)}: {pane.title}]
                    </span>
                </div>

                <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="hover:text-white p-1 hover:bg-white/5 rounded"><Maximize2 size={12} /></button>
                    {!pane.isSticky && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                commandBus.dispatch({
                                    name: COMMAND_NAMES.REMOVE_PANE,
                                    args: [],
                                    context: { sourceId: pane.id, focusedPaneId }
                                });
                            }}
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

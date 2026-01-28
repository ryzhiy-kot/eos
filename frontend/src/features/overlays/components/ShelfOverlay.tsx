/**
 * PROJECT: MONAD
 * AUTHOR: Kyrylo Yatsenko
 * YEAR: 2026
 * * COPYRIGHT NOTICE:
 * © 2026 Kyrylo Yatsenko. All rights reserved.
 * 
 * This work represents a proprietary methodology for Human-Machine Interaction (HMI).
 * All source code, logic structures, and User Experience (UX) frameworks
 * contained herein are the sole intellectual property of Kyrylo Yatsenko.
 * 
 * ATTRIBUTION REQUIREMENT:
 * Any use of this program, or any portion thereof (including code snippets and
 * interaction patterns), may not be used, redistributed, or adapted
 * without explicit, visible credit to Kyrylo Yatsenko as the original author.
 */

import React from 'react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { MonitorPlay } from 'lucide-react';
import clsx from 'clsx';
import ContentFactory from '@/components/panes/ContentFactory';
import { commandBus, COMMAND_NAMES } from '@/lib/commandBus';
import LookupOverlay from '@/features/overlays/components/LookupOverlay';
import { Pane } from '@/store/workspaceStore';

const ShelfOverlay: React.FC = () => {
    const { archive, panes, activeOverlay, focusedPaneId } = useWorkspaceStore();
    const isOpen = activeOverlay === 'shelf';

    const handleSelect = (pane: Pane) => {
        commandBus.dispatch({
            name: COMMAND_NAMES.SHOW,
            args: [pane.id],
            context: { sourceId: pane.id, focusedPaneId }
        });
    };

    const filterItem = (id: string, query: string) => {
        const pane = panes[id];
        if (!pane) return false;
        const q = query.toLowerCase();
        return pane.title.toLowerCase().includes(q) || pane.id.toLowerCase().includes(q);
    };

    const renderItem = (id: string, isSelected: boolean) => {
        const pane = panes[id];
        if (!pane) return null;
        return (
            <div
                className={clsx(
                    "group bg-neutral-900 border rounded-lg overflow-hidden transition-all flex flex-col h-64",
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
        );
    };

    return (
        <LookupOverlay<string>
            title="The Shelf"
            subtitle={`${archive.length} Items`}
            isOpen={isOpen}
            onClose={() => commandBus.dispatch({ name: COMMAND_NAMES.LS, args: ['close'], context: { focusedPaneId } })}
            items={archive}
            renderItem={renderItem}
            onSelect={(id) => handleSelect(panes[id])}
            filterItem={filterItem}
            placeholder="Filter shelf..."
            gridCols={4}
            maxWidth="max-w-none"
            contentWidth="max-w-7xl"
            emptyMessage="No items found in the archive."
        />
    );
};

export default ShelfOverlay;

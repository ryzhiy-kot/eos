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
import { useWorkspaceStore, workspaceActions } from '@/store/workspaceStore';
import { Terminal, ArrowRight } from 'lucide-react';
import { formatCommandUsage, CommandEntry } from '@/lib/commandRegistry';
import { commandBus, COMMAND_NAMES } from '@/lib/commandBus';
import clsx from 'clsx';
import LookupOverlay from '@/features/overlays/components/LookupOverlay';

const HelpOverlay: React.FC = () => {
    const { activeOverlay, commands, focusedPaneId } = useWorkspaceStore();
    const isOpen = activeOverlay === 'help';

    const handleSelect = (item: CommandEntry) => {
        workspaceActions.setPendingCommand(`/${item.name} `);
        commandBus.dispatch({ name: COMMAND_NAMES.HELP, args: ['close'], context: { focusedPaneId } });
    };

    const filterItem = (item: CommandEntry, query: string) => {
        const q = query.toLowerCase();
        return item.name.toLowerCase().includes(q) || item.description.toLowerCase().includes(q);
    };

    const renderItem = (c: CommandEntry, isSelected: boolean) => (
        <div
            className={clsx(
                "group flex items-center justify-between p-4 rounded-lg border transition-all",
                isSelected
                    ? "border-blue-500 bg-neutral-900"
                    : "border-neutral-800 hover:border-neutral-600 hover:bg-neutral-900/50"
            )}
        >
            <div className="flex items-center space-x-4">
                <div className={clsx(
                    "p-2 rounded transition-colors",
                    isSelected ? "bg-blue-500/10 text-blue-400" : "bg-neutral-800 text-neutral-400"
                )}>
                    <Terminal size={20} />
                </div>
                <div>
                    <div className={clsx(
                        "font-mono font-bold text-lg transition-colors",
                        isSelected ? "text-blue-400" : "text-white"
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
                isSelected ? "text-white" : "text-neutral-700 group-hover:text-neutral-500"
            )} />
        </div>
    );

    return (
        <LookupOverlay<CommandEntry>
            title="Command Center (Help)"
            subtitle="Registry-Driven"
            isOpen={isOpen}
            onClose={() => commandBus.dispatch({ name: COMMAND_NAMES.HELP, args: ['close'], context: { focusedPaneId } })}
            items={commands}
            renderItem={renderItem}
            onSelect={handleSelect}
            filterItem={filterItem}
            placeholder="Search commands..."
            emptyMessage={commands.length === 0 ? "Registry is empty. Commands are being initialized..." : "No commands found matching your search."}
        />
    );
};

export default HelpOverlay;

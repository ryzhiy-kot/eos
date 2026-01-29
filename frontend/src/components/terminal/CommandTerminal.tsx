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
import { useHotkeys } from 'react-hotkeys-hook';
import { CommandEntry } from '@/lib/commandRegistry';
import { useCommandTerminal } from '@/hooks/useCommandTerminal';
import TerminalInput from '@/components/terminal/TerminalInput';
import TerminalStatus from '@/components/terminal/TerminalStatus';
import TerminalNotification from '@/components/terminal/TerminalNotification';
import { COMMAND_NAMES, commandBus } from '@/lib/commandBus';

const ShortcutHandler: React.FC<{
    cmd: CommandEntry;
    onTrigger: (name: string) => void;
    onPopulate: (name: string) => void;
}> = ({ cmd, onTrigger, onPopulate }) => {
    useHotkeys(cmd.shortcut!, (e) => {
        e.preventDefault();
        const hasParams = cmd.parameters?.some(p => p.required);
        if (hasParams || cmd.category === 'data') {
            onPopulate(cmd.name);
        } else {
            onTrigger(cmd.name);
        }
    }, { enableOnFormTags: cmd.shortcut === 'ctrl+/' });
    return null;
};

const CommandTerminal: React.FC = () => {
    // 1. Terminal logic (input, execution, focus, files)
    const {
        input, setInput,
        isLoading,
        handleSubmit,
        handleFileSelect,
        inputRef,
        fileInputRef,
        activePaneId
    } = useCommandTerminal();

    const { commands, panes } = useWorkspaceStore();

    const activePane = activePaneId ? panes[activePaneId] : null;

    return (
        <div className="relative bg-panel-light dark:bg-panel-dark rounded p-4 flex items-center gap-3 transition-all duration-300">
            {/* Dynamic Shortcut Registration */}
            {commands.map(cmd => cmd.shortcut && (
                <ShortcutHandler
                    key={cmd.name}
                    cmd={cmd}
                    onTrigger={(name) => commandBus.dispatch({ name: COMMAND_NAMES.SHOW, args: [name], context: { sourceId: name, focusedPaneId: activePaneId } })}
                    onPopulate={(name) => {
                        setInput(`/${name} `);
                    }}
                />
            ))}

            {/* Notification Section */}
            <div className="absolute left-4 right-4 bottom-full mb-1">
                <TerminalNotification />
            </div>

            {/* Input Section */}
            <TerminalInput
                input={input}
                setInput={setInput}
                isLoading={isLoading}
                inputRef={inputRef}
                fileInputRef={fileInputRef}
                onSubmit={handleSubmit}
                onFileSelect={handleFileSelect}
                activePaneId={activePaneId}
                paneType={activePane?.type}
            />

            {/* Status Section */}
            <TerminalStatus isLoading={isLoading} />
        </div>
    );
};

export default CommandTerminal;

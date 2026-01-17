import React from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { useHotkeys } from 'react-hotkeys-hook';
import { CommandEntry } from '../../lib/commandRegistry';
import { useRegisterCommands } from '../../hooks/useRegisterCommands';
import { useCommandTerminal } from '../../hooks/useCommandTerminal';
import TerminalInput from './TerminalInput';
import TerminalStatus from './TerminalStatus';

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
    // 1. Register all system/data commands
    useRegisterCommands();

    // 2. Terminal logic (input, execution, focus, files)
    const {
        input, setInput,
        isLoading,
        inputRef, fileInputRef,
        handleSubmit,
        handleFileSelect,
        processCommandString,
        activePaneId
    } = useCommandTerminal();

    const { commands, panes } = useWorkspaceStore();

    const activePane = activePaneId ? panes[activePaneId] : null;

    return (
        <div className="bg-panel-light dark:bg-panel-dark rounded p-4 flex items-center gap-3 transition-all duration-300">
            {/* Dynamic Shortcut Registration */}
            {commands.map(cmd => cmd.shortcut && (
                <ShortcutHandler
                    key={cmd.name}
                    cmd={cmd}
                    onTrigger={(name) => processCommandString(`/${name}`)}
                    onPopulate={(name) => {
                        setInput(`/${name} `);
                        inputRef.current?.focus();
                    }}
                />
            ))}

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

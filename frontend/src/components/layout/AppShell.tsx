import React from 'react';
import ChronoHeader from './ChronoHeader';
import WorkspaceGrid from '../grid/WorkspaceGrid';
import CommandTerminal from '../terminal/CommandTerminal';
import ArchiveOverlay from './ArchiveOverlay';
import HelpOverlay from './HelpOverlay';
import { useRegisterCommands } from '../../hooks/useRegisterCommands';

const AppShell: React.FC = () => {
    const [isRegistryReady, setIsRegistryReady] = React.useState(false);

    // Register commands at the top level and track readiness
    useRegisterCommands(() => setIsRegistryReady(true));

    return (
        <div className="flex flex-col h-screen w-screen bg-black text-white overflow-hidden font-mono relative">
            <ArchiveOverlay />
            <HelpOverlay />

            <ChronoHeader />

            <main className="flex-1 relative overflow-hidden p-2">
                {isRegistryReady && <WorkspaceGrid />}
            </main>

            <div className="h-16 border-t border-neutral-800 bg-neutral-950 p-2">
                <CommandTerminal />
            </div>
        </div>
    );
};

export default AppShell;

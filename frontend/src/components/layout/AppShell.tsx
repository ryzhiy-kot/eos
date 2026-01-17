import React from 'react';
import ChronoHeader from './ChronoHeader';
import WorkspaceGrid from '../grid/WorkspaceGrid';
import CommandTerminal from '../terminal/CommandTerminal';

const AppShell: React.FC = () => {
    return (
        <div className="flex flex-col h-screen w-screen bg-black text-white overflow-hidden font-mono">
            {/* Top: Header */}
            <ChronoHeader />

            {/* Center: Dynamic Grid */}
            <main className="flex-1 relative overflow-hidden p-2">
                <WorkspaceGrid />
            </main>

            {/* Bottom: Terminal */}
            <div className="h-16 border-t border-neutral-800 bg-neutral-950 p-2">
                <CommandTerminal />
            </div>
        </div>
    );
};

export default AppShell;

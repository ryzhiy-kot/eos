import React from 'react';
import Header from './Header';
import WorkspaceGrid from '../grid/WorkspaceGrid';
import CommandTerminal from '../terminal/CommandTerminal';
import { ShelfOverlay, HelpOverlay } from '@/features/overlays';
import { useRegisterCommands } from '@/hooks/useRegisterCommands';
import { useSSE } from '@/hooks/useSSE';
import { useWorkspaceSync } from '@/hooks/useWorkspaceSync';
import { useWorkspaceStore } from '@/store/workspaceStore';

const AppShell: React.FC = () => {
    const { activeOverlay } = useWorkspaceStore();
    const [isRegistryReady, setIsRegistryReady] = React.useState(false);

    // Initialize SSE connection for real-time communication
    const { status: connectionStatus } = useSSE({
        onMessage: (message) => {
            // Handle different message types
            if (message.type === 'notification') {
                console.log('SSE notification:', message);
            }
        },
        onError: (error) => {
            console.error('SSE error:', error);
        }
    });

    // Sync Workspace State
    useWorkspaceSync();

    // Register commands at the top level and track readiness
    useRegisterCommands(() => setIsRegistryReady(true));

    return (
        <div className="flex flex-col h-screen w-screen bg-black text-white overflow-hidden font-mono relative">
            {activeOverlay === 'shelf' && <ShelfOverlay />}
            {activeOverlay === 'help' && <HelpOverlay />}

            <Header connectionStatus={connectionStatus} />

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

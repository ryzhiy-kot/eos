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

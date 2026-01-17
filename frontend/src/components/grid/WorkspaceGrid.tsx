import React, { useEffect } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import PaneFrame from '../panes/PaneFrame';

const WorkspaceGrid: React.FC = () => {
    const { panes, activeLayout, addPane } = useWorkspaceStore();

    // Initial pane for testing/bootstrapping
    useEffect(() => {
        if (activeLayout.length === 0) {
            addPane({
                id: 'P1',
                type: 'chat',
                title: 'System Initialized',
                content: [{ role: 'system', content: 'Welcome to Elyon. System ready.' }],
                isSticky: true,
                lineage: { parentIds: [], command: 'init', timestamp: new Date().toISOString() }
            });
        }
    }, [activeLayout.length, addPane]);

    const getGridStyles = (count: number) => {
        // Tailwind arbitrary values for grid template
        if (count <= 1) return 'grid-cols-1 grid-rows-1';
        if (count === 2) return 'grid-cols-2 grid-rows-1';
        if (count <= 4) return 'grid-cols-2 grid-rows-2';
        return 'grid-cols-3 grid-rows-3';
    };

    return (
        <div className={`h-full w-full grid gap-2 ${getGridStyles(activeLayout.length)} transition-all duration-300 ease-in-out`}>
            {activeLayout.map((paneId) => {
                const pane = panes[paneId];
                if (!pane) return null;
                return <PaneFrame key={paneId} pane={pane} />;
            })}
        </div>
    );
};

export default WorkspaceGrid;

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

import React, { useEffect } from 'react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import PaneFrame from '@/components/panes/PaneFrame';
import { commandBus, COMMAND_NAMES } from '@/lib/commandBus';
import ErrorBoundary from '../common/ErrorBoundary';
import PaneErrorFallback from '../panes/PaneErrorFallback';

const WorkspaceGrid: React.FC = () => {
    const { panes, activeLayout } = useWorkspaceStore();

    // Initial pane for testing/bootstrapping
    useEffect(() => {
        if (activeLayout.length === 0) {
            commandBus.dispatch({ name: COMMAND_NAMES.INIT, args: [], context: { focusedPaneId: null } });
        }
    }, [activeLayout.length]);

    // Base 6 grid allows for perfect 2-item (3+3) and 3-item (2+2+2) rows
    const getContainerClass = (count: number) => {
        if (count <= 1) return 'grid-cols-1 grid-rows-1';
        if (count === 2) return 'grid-cols-2 grid-rows-1'; // Side-by-side

        // 3-4 items: 2 rows
        if (count <= 4) return 'grid-cols-6 grid-rows-2';

        // 5-6 items: 2 rows (3 on top, 2 or 3 on bottom)
        if (count <= 6) return 'grid-cols-6 grid-rows-2';

        // 7-9 items: 3 rows
        return 'grid-cols-6 grid-rows-3';
    };

    const getItemSpan = (index: number, total: number) => {
        if (total <= 1) return ''; // Default
        if (total === 2) return ''; // Default 1 col each in 2-col grid

        // For standard 2x2 (4 items) -> all span 3
        if (total === 4) return 'col-span-3';

        // Complex cases with Base 6

        // 3 Items: Top 2 (span 3), Bottom 1 (span 6)
        if (total === 3) {
            return index === 2 ? 'col-span-6' : 'col-span-3';
        }

        // 5 Items: Top 3 (span 2), Bottom 2 (span 3)
        if (total === 5) {
            return index >= 3 ? 'col-span-3' : 'col-span-2';
        }

        // 6 Items: All span 2
        if (total === 6) return 'col-span-2';

        // 7 Items: Top 3 (span 2), Middle 3 (span 2), Bottom 1 (span 6)
        if (total === 7) {
            return index === 6 ? 'col-span-6' : 'col-span-2';
        }

        // 8 Items: Top 3 (span 2), Middle 3 (span 2), Bottom 2 (span 3)
        if (total === 8) {
            return index >= 6 ? 'col-span-3' : 'col-span-2';
        }

        // 9 Items: All span 2
        if (total === 9) return 'col-span-2';

        return 'col-span-2'; // Default fallback
    };

    return (
        <div className={`h-full w-full grid gap-2 ${getContainerClass(activeLayout.length)} transition-all duration-300 ease-in-out`}>
            {activeLayout.map((paneId, index) => {
                const pane = panes[paneId];
                if (!pane) return null;
                return (
                    <div key={paneId} className={`${getItemSpan(index, activeLayout.length)} overflow-hidden`}>
                        <ErrorBoundary
                            fallback={({ error, reset }) => (
                                <PaneErrorFallback
                                    error={error}
                                    reset={reset}
                                />
                            )}
                        >
                            <PaneFrame pane={pane} />
                        </ErrorBoundary>
                    </div>
                );
            })}
        </div>
    );
};

export default WorkspaceGrid;

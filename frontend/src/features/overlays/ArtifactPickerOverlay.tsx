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

import React, { useMemo } from 'react';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { FileText, Image, Code, Database, MessageSquare } from 'lucide-react';
import clsx from 'clsx';
import { commandBus, COMMAND_NAMES } from '@/lib/commandBus';
import LookupOverlay from '@/features/overlays/components/LookupOverlay';
import { PaneType, OverlayType } from '@/types/constants';
import { Artifact } from '@/store/workspaceStore';

const ArtifactPickerOverlay: React.FC = () => {
    const { artifacts, activeOverlay, focusedPaneId, panes, artifactPickerMode } = useWorkspaceStore();
    const isOpen = activeOverlay === OverlayType.ARTIFACT_PICKER;

    const filteredArtifacts = useMemo(() => {
        if (!isOpen) return [];

        const allArtifacts = Object.values(artifacts);

        if (artifactPickerMode === 'all') {
            return allArtifacts;
        }

        // 'session' mode: Filter by session of the focused pane
        const focusedPane = focusedPaneId ? panes[focusedPaneId] : null;
        if (!focusedPane) return []; // Fallback? or show none?

        // 1. Get current pane's artifact
        const currentArtifact = artifacts[focusedPane.artifactId];
        if (!currentArtifact || !currentArtifact.session_id) return [];

        // 2. Filter artifacts with matching session_id
        return allArtifacts.filter(a => a.session_id === currentArtifact.session_id);

    }, [isOpen, artifacts, focusedPaneId, panes, artifactPickerMode]);

    const handleSelect = (artifact: Artifact) => {
        commandBus.dispatch({
            name: COMMAND_NAMES.OPEN,
            args: [artifact.id],
            context: { focusedPaneId }
        });
    };

    const getIcon = (type: string) => {
        switch (type) {
            case PaneType.CHAT: return <MessageSquare size={16} />;
            case PaneType.CODE: return <Code size={16} />;
            case PaneType.VISUAL: return <Image size={16} />;
            case PaneType.DATA: return <Database size={16} />;
            default: return <FileText size={16} />;
        }
    };

    const filterItem = (artifact: Artifact, query: string) => {
        const q = query.toLowerCase();
        return (
            artifact.id.toLowerCase().includes(q) ||
            (artifact.metadata?.filename || '').toLowerCase().includes(q) ||
            artifact.type.toLowerCase().includes(q)
        );
    };

    const renderItem = (artifact: Artifact, isSelected: boolean) => {
        return (
            <div
                className={clsx(
                    "group bg-neutral-900 border rounded-lg overflow-hidden transition-all flex flex-col h-32 p-4 cursor-pointer",
                    isSelected
                        ? "border-blue-500 scale-[1.02] ring-2 ring-blue-500/50 shadow-lg shadow-blue-500/20"
                        : "border-neutral-800 hover:border-neutral-600 hover:scale-[1.02]"
                )}
            >
                <div className="flex items-center gap-2 mb-2">
                    <span className={clsx(
                        isSelected ? "text-blue-400" : "text-neutral-500"
                    )}>
                        {getIcon(artifact.type)}
                    </span>
                    <span className={clsx(
                        "font-bold font-mono text-xs truncate flex-1",
                        isSelected ? "text-blue-300" : "text-neutral-300"
                    )}>
                        {artifact.metadata?.filename || artifact.id}
                    </span>
                    <span className="text-[10px] text-neutral-600 uppercase font-mono">
                        {artifact.type}
                    </span>
                </div>

                <div className="flex-1 text-[10px] text-neutral-500 overflow-hidden">
                    {/* Preview logic could go here, e.g. snippet of code or chat */}
                    <p className="line-clamp-3">
                         {JSON.stringify(artifact.payload).substring(0, 150)}
                    </p>
                </div>

                 <div className="mt-2 text-[9px] text-neutral-600 font-mono text-right">
                    {artifact.created_at ? new Date(artifact.created_at).toLocaleString() : 'Just now'}
                </div>
            </div>
        );
    };

    return (
        <LookupOverlay<Artifact>
            title={artifactPickerMode === 'all' ? "All Artifacts" : "Session Artifacts"}
            subtitle={`${filteredArtifacts.length} Items`}
            isOpen={isOpen}
            onClose={() => commandBus.dispatch({ name: COMMAND_NAMES.OPEN, args: ['close'], context: { focusedPaneId } })}
            items={filteredArtifacts}
            renderItem={renderItem}
            onSelect={handleSelect}
            filterItem={filterItem}
            placeholder="Filter artifacts..."
            gridCols={3}
            maxWidth="max-w-none"
            contentWidth="max-w-6xl"
            emptyMessage={filteredArtifacts.length === 0 ? "No artifacts found." : "No matching artifacts."}
        />
    );
};

export default ArtifactPickerOverlay;

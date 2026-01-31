/**
 * PROJECT: EoS
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
import { useWorkspaceStore, Pane, workspaceActions } from '../../store/workspaceStore';
import CodeRenderer from '../renderers/CodeRenderer';
import MarkdownRenderer from '../renderers/MarkdownRenderer';
import PDFRenderer from '../renderers/PDFRenderer';
import DataGridRenderer from '../renderers/DataGridRenderer';
import VisualRenderer from '../renderers/VisualRenderer';
import ChatRenderer from '../renderers/ChatRenderer';
import { PaneType, MutationStatus } from '@/types/constants';

interface ContentFactoryProps {
    pane: Pane;
}

const ContentFactory: React.FC<ContentFactoryProps> = ({ pane }) => {
    const { artifacts, activeVersions } = useWorkspaceStore();
    const artifact = artifacts[pane.artifactId];
    const activeVersionId = activeVersions[pane.artifactId];

    if (!artifact) {
        return (
            <div className="p-4 flex flex-col items-center justify-center h-full text-neutral-600 font-mono text-xs gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
                LOADING: {pane.title}
            </div>
        );
    }

    // Resolve what to display based on active versionId
    const currentMutation = artifact.mutations?.find(m => m.version_id === activeVersionId);
    const displayPayload = currentMutation ? currentMutation.payload : artifact.payload;
    const isGhost = currentMutation?.status === MutationStatus.GHOST;

    const renderVersionToolbar = () => {
        if (!isGhost) return null;
        return (
            <div className="absolute top-2 right-2 flex gap-2 z-10 bg-amber-100 dark:bg-amber-900/50 border border-amber-500/50 p-2 rounded-lg shadow-lg backdrop-blur-md">
                <span className="text-[10px] uppercase font-bold text-amber-600 dark:text-amber-400 mr-2 flex items-center">
                    Ghost Preview ({activeVersionId})
                </span>
                <button
                    onClick={() => workspaceActions.commitMutation(artifact.id, { ...currentMutation!, status: MutationStatus.COMMITTED })}
                    className="px-2 py-1 bg-accent-green text-white text-[10px] rounded hover:bg-green-600 transition-colors uppercase font-bold"
                >
                    Accept
                </button>
                <button
                    onClick={() => workspaceActions.setArtifactVersion(artifact.id, currentMutation?.parent_id || 'v1')}
                    className="px-2 py-1 bg-red-500 text-white text-[10px] rounded hover:bg-red-600 transition-colors uppercase font-bold"
                >
                    Discard
                </button>
            </div>
        );
    };

    const contentClass = `flex-1 flex flex-col h-full relative transition-all duration-300 ${isGhost ? 'bg-amber-50/10 dark:bg-amber-950/10 ring-2 ring-amber-500/20' : ''}`;

    const renderMainContent = () => {
        switch (pane.type) {
            case PaneType.CHAT:
                return (
                    <ChatRenderer
                        messages={displayPayload?.messages}
                        contextDescription={artifact.metadata?.context_description}
                    />
                );
            case PaneType.DATA:
                return <DataGridRenderer data={displayPayload.data} />;
            case PaneType.CODE:
                return <CodeRenderer content={displayPayload.source} language={displayPayload.language || "python"} />;
            case PaneType.DOC:
                if (displayPayload.format === 'pdf' || displayPayload.is_url) {
                    return <PDFRenderer url={displayPayload.value} />;
                }
                return <MarkdownRenderer content={String(displayPayload.value)} />;
            case PaneType.VISUAL:
                return <VisualRenderer src={displayPayload.url} title={pane.title} />;
            default:
                return (
                    <div className="p-4 flex items-center justify-center h-full text-neutral-600 font-mono text-xs">
                        UNKNOWN PANE TYPE: {pane.type}
                    </div>
                );
        }
    };

    return (
        <div className={contentClass}>
            {renderVersionToolbar()}
            {renderMainContent()}

            {/* Version Filmstrip Shortcut/Label */}
            {!isGhost && artifact.mutations?.length > 1 && (
                <div className="absolute bottom-2 right-2 text-[8px] font-mono text-neutral-400 dark:text-neutral-600 bg-black/5 p-1 rounded backdrop-blur-sm group-hover:opacity-100">
                    VERSION: {activeVersionId} OF {artifact.mutations.length}
                </div>
            )}
        </div>
    );
};

export default ContentFactory;

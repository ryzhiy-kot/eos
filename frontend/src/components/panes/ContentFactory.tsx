import React from 'react';
import { useWorkspaceStore, Pane, workspaceActions } from '../../store/workspaceStore';
import CodeRenderer from '../renderers/CodeRenderer';
import MarkdownRenderer from '../renderers/MarkdownRenderer';
import ReactMarkdown from 'react-markdown';
import PDFRenderer from '../renderers/PDFRenderer';
import DataGridRenderer from '../renderers/DataGridRenderer';
import VisualRenderer from '../renderers/VisualRenderer';

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
                LOADING ARTIFACT: {pane.artifactId}
            </div>
        );
    }

    // Resolve what to display based on active versionId
    const currentMutation = artifact.mutations?.find(m => m.version_id === activeVersionId);
    const displayPayload = currentMutation ? currentMutation.payload : artifact.payload;
    const isGhost = currentMutation?.status === 'ghost';

    const renderVersionToolbar = () => {
        if (!isGhost) return null;
        return (
            <div className="absolute top-2 right-2 flex gap-2 z-10 bg-amber-100 dark:bg-amber-900/50 border border-amber-500/50 p-2 rounded-lg shadow-lg backdrop-blur-md">
                <span className="text-[10px] uppercase font-bold text-amber-600 dark:text-amber-400 mr-2 flex items-center">
                    Ghost Preview ({activeVersionId})
                </span>
                <button
                    onClick={() => workspaceActions.commitMutation(artifact.id, { ...currentMutation!, status: 'committed' })}
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
            case 'chat':
                return (
                    <div className="flex-1 overflow-y-auto p-4 space-y-6 text-sm">
                        <div className="text-slate-500 border-l-2 border-border-light dark:border-border-dark pl-3 italic text-xs">
                            Context: {artifact.metadata?.context_description || "Dynamic Session"}
                        </div>

                        {displayPayload?.messages && Array.isArray(displayPayload.messages) ? (
                            displayPayload.messages.map((msg: any, i: number) => {
                                const isUser = msg.role === 'user';
                                return (
                                    <div key={i} className="flex gap-4">
                                        <div className={`w-20 flex-shrink-0 font-bold ${isUser ? 'text-accent-green' : 'text-primary'}`}>
                                            {isUser ? 'User' : 'Assistant'}
                                        </div>
                                        <div className="text-slate-700 dark:text-slate-300 leading-relaxed prose prose-invert prose-sm max-w-none [&>*:first-child]:mt-0">
                                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            {msg.artifacts && msg.artifacts.length > 0 && (
                                                <div className="mt-2 flex flex-wrap gap-2">
                                                    {msg.artifacts.map((art: any) => (
                                                        <span key={art.id} className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-200 dark:border-neutral-700">
                                                            📎 {art.id}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <div className="opacity-50 italic">New conversation started...</div>
                        )}
                    </div>
                );
            case 'data':
                return <DataGridRenderer data={displayPayload.data} />;
            case 'code':
                return <CodeRenderer content={displayPayload.source} language={displayPayload.language || "python"} />;
            case 'doc':
                if (displayPayload.format === 'pdf' || displayPayload.is_url) {
                    return <PDFRenderer url={displayPayload.value} />;
                }
                return <MarkdownRenderer content={String(displayPayload.value)} />;
            case 'visual':
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

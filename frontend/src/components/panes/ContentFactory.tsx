import React from 'react';
import { Pane } from '../../store/workspaceStore';
import CodeRenderer from '../renderers/CodeRenderer';
import MarkdownRenderer from '../renderers/MarkdownRenderer';
import PDFRenderer from '../renderers/PDFRenderer';
import DataGridRenderer from '../renderers/DataGridRenderer';
import VisualRenderer from '../renderers/VisualRenderer';

interface ContentFactoryProps {
    pane: Pane;
}

const ContentFactory: React.FC<ContentFactoryProps> = ({ pane }) => {
    switch (pane.type) {
        case 'chat':
            // Chat is a list of messages. We'll render them as markdown bubbles.
            return (
                <div className="p-4 h-full overflow-y-auto text-sm font-mono text-neutral-300 space-y-4">
                    {Array.isArray(pane.content) ? (
                        pane.content.map((msg: any, i: number) => (
                            <div key={i} className="flex flex-col">
                                <span className={`font-bold uppercase text-xs mb-1 ${msg.role === 'user' ? 'text-blue-400' : 'text-emerald-400'}`}>
                                    [{msg.role === 'user' ? 'User' : 'AI'}]
                                </span>
                                <div className="bg-neutral-800/50 p-3 rounded border border-neutral-800/50">
                                    <MarkdownRenderer content={msg.content} />
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="opacity-50 italic">New conversation started...</div>
                    )}
                </div>
            );
        case 'data':
            return <DataGridRenderer data={pane.content} />;
        case 'code':
            // If content is just string
            const codeContent = typeof pane.content === 'string' ? pane.content : JSON.stringify(pane.content, null, 2);
            return <CodeRenderer content={codeContent} language="python" />;
        case 'doc':
            // Assume content is a URL for PDF or text for Markdown doc
            if (typeof pane.content === 'string' && pane.content.startsWith('blob:')) {
                return <PDFRenderer url={pane.content} />;
            }
            return <MarkdownRenderer content={String(pane.content)} />;
        case 'visual':
            const imgSrc = typeof pane.content === 'string' ? pane.content : (pane.content?.url || pane.content?.src || '');
            return <VisualRenderer src={imgSrc} title={pane.title} />;
        default:
            return (
                <div className="p-4 flex items-center justify-center h-full text-neutral-600 font-mono text-xs">
                    UNKNOWN PANE TYPE: {pane.type}
                </div>
            );
    }
};

export default ContentFactory;

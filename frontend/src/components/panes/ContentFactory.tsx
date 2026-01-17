import React from 'react';
import { Pane } from '../../store/workspaceStore';
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
    switch (pane.type) {
        case 'chat':
            // Chat is a list of messages. We'll render them as markdown bubbles.
            return (
                <div className="flex-1 overflow-y-auto p-4 space-y-6 text-sm">
                    {/* Optional Context Header Placeholder */}
                    <div className="text-slate-500 border-l-2 border-border-light dark:border-border-dark pl-3 italic text-xs">
                        Context: System initialized.
                    </div>

                    {Array.isArray(pane.content) ? (
                        pane.content.map((msg: any, i: number) => {
                            const isUser = msg.role === 'user';
                            return (
                                <div key={i} className="flex gap-4">
                                    <div className={`w-20 flex-shrink-0 font-bold ${isUser ? 'text-accent-green' : 'text-primary'}`}>
                                        {isUser ? 'User' : 'Assistant'}
                                    </div>
                                    <div className="text-slate-700 dark:text-slate-300 leading-relaxed prose prose-invert prose-sm max-w-none [&>*:first-child]:mt-0">
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
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

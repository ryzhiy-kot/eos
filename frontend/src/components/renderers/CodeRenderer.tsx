import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeRendererProps {
    content: string;
    language?: string;
}

const CodeRenderer: React.FC<CodeRendererProps> = ({ content, language = 'javascript' }) => {
    return (
        <div className="h-full w-full overflow-hidden text-sm">
            <SyntaxHighlighter
                language={language}
                style={vscDarkPlus}
                customStyle={{ margin: 0, height: '100%', padding: '1rem', background: '#0a0a0a' }}
                showLineNumbers={true}
            >
                {content}
            </SyntaxHighlighter>
        </div>
    );
};

export default CodeRenderer;

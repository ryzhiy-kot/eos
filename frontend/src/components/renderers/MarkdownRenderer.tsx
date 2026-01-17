import React from 'react';
import ReactMarkdown from 'react-markdown';
// import rehypeRaw from 'rehype-raw'; // Optional, skipping for security/simplicity unless needed

interface MarkdownRendererProps {
    content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
    return (
        <div className="h-full w-full overflow-y-auto p-4 prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
        </div>
    );
};

export default MarkdownRenderer;

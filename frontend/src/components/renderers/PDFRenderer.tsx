import React from 'react';

interface PDFRendererProps {
    url: string; // Blob URL or remote URL
}

const PDFRenderer: React.FC<PDFRendererProps> = ({ url }) => {
    return (
        <div className="h-full w-full bg-neutral-800 flex flex-col">
            <iframe
                src={url}
                className="w-full flex-1 border-none"
                title="PDF Viewer"
            />
        </div>
    );
};

export default PDFRenderer;

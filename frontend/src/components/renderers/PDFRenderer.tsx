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

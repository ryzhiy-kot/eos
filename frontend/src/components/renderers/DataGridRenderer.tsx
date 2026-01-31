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
import { List, RowComponentProps } from 'react-window';
import { AutoSizer } from 'react-virtualized-auto-sizer';

interface DataGridRendererProps {
    data: any[];
}

// Row component defined outside to avoid re-creation
const Row = ({ index, style, ariaAttributes, data, headers }: RowComponentProps<{ data: any[], headers: string[] }>) => {
    const row = data[index];
    const minWidth = headers.length * 150;

    return (
        <div
            {...ariaAttributes}
            style={{ ...style, width: typeof style.width === 'number' ? Math.max(style.width, minWidth) : minWidth }}
            className="flex items-center hover:bg-white/5 transition-colors border-b border-neutral-800 text-neutral-400"
        >
            {headers.map((header: string) => (
                <div
                    key={`${index}-${header}`}
                    className="px-4 py-2 whitespace-nowrap overflow-hidden text-ellipsis border-r border-neutral-800 last:border-r-0 flex-1 min-w-[150px]"
                    title={typeof row[header] === 'object' ? JSON.stringify(row[header]) : String(row[header])}
                >
                    {typeof row[header] === 'object' ? JSON.stringify(row[header]) : String(row[header])}
                </div>
            ))}
        </div>
    );
};

const DataGridRenderer: React.FC<DataGridRendererProps> = ({ data }) => {
    if (!data || data.length === 0) return <div className="p-4 text-neutral-500">No data available</div>;

    const headers = Object.keys(data[0]);
    const headerRef = React.useRef<HTMLDivElement>(null);
    const listRef = React.useRef<any>(null);

    React.useEffect(() => {
        // Wait for listRef to be populated and element available
        const attachListener = () => {
            const listInstance = listRef.current;
            // Depending on react-window version/bundling, element might be directly on ref or .outerRef
            // Typically List ref exposes methods, but we need the outer DOM node for scroll event.
            // react-window passes outerRef to the outer div.

            // Let's try to find the outer element.
            // Note: FixedSizeList does not expose 'element' property on the ref instance directly in types,
            // but usually it works if we used outerRef prop.
            // But we can't easily access the DOM node from the ref instance unless we use outerRef prop.

            // Revert strategy: Use `outerRef` prop but attach it to a MutableRefObject that we control.
        };
    }, []);

    // New strategy: Pass a ref callback to outerRef
    const outerRefCallback = React.useCallback((node: HTMLElement | null) => {
        if (node) {
            // Use addEventListener instead of onscroll property to avoid overwriting existing listeners if any
            const handleScroll = (e: Event) => {
                if (headerRef.current) {
                    headerRef.current.scrollLeft = (e.target as HTMLElement).scrollLeft;
                }
            };
            node.addEventListener('scroll', handleScroll);
            // Cleanup not easily possible with this callback pattern unless we store the node and listener...
            // But since DataGridRenderer mounts/unmounts, the node will be garbage collected.
            // A better way is strictly attaching once.
            // But to be safe, setting onscroll directly is actually cleaner for this use case if we own the scroll behavior.

            node.onscroll = (e: any) => {
                if (headerRef.current) {
                    headerRef.current.scrollLeft = e.target.scrollLeft;
                }
            };
        }
    }, []);

    return (
        <div className="h-full w-full bg-neutral-900 flex flex-col font-mono text-xs">
            {/* Header */}
            <div
                ref={headerRef}
                className="flex bg-neutral-800 text-neutral-300 border-b border-neutral-700 overflow-hidden"
            >
                {headers.map((header) => (
                    <div
                        key={header}
                        className="px-4 py-2 font-medium uppercase tracking-wider border-r border-neutral-700 last:border-r-0 flex-1 min-w-[150px]"
                    >
                        {header}
                    </div>
                ))}
            </div>

            {/* Body */}
            <div className="flex-1">
                <AutoSizer
                    renderProp={({ height, width }: any) => {
                        if (!height || !width) return null;
                        return (
                            <List
                                style={{ height, width }}
                                rowCount={data.length}
                                rowHeight={40}
                                listRef={outerRefCallback as any}
                                className="overflow-y-auto overflow-x-auto"
                                rowComponent={Row}
                                rowProps={{ data, headers }}
                            />
                        );
                    }}
                />
            </div>
        </div>
    );
};

export default DataGridRenderer;

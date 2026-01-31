import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DataGridRenderer from './DataGridRenderer';

// Mock AutoSizer
vi.mock('react-virtualized-auto-sizer', () => ({
    AutoSizer: ({ renderProp }: any) => renderProp({ height: 600, width: 800 }),
}));

// Mock react-window List
vi.mock('react-window', () => ({
    List: ({ rowCount, rowHeight, rowComponent: RowComponent, rowProps, style, listRef, ...props }: any) => {
        const height = style?.height || 600;
        const visibleCount = Math.ceil(height / rowHeight);
        const items = [];
        for (let i = 0; i < Math.min(rowCount, visibleCount); i++) {
            items.push(
                <React.Fragment key={i}>
                    {RowComponent({
                        index: i,
                        style: { height: rowHeight, width: '100%', top: i * rowHeight },
                        ariaAttributes: { "aria-posinset": i + 1, "aria-setsize": rowCount, role: "listitem" },
                        ...rowProps
                    })}
                </React.Fragment>
            );
        }
        return <div data-testid="virtual-list" style={style} {...props}>{items}</div>;
    },
}));

// Mock data generator
const generateData = (count: number) => {
    return Array.from({ length: count }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        value: Math.random() * 1000,
        description: `Description for item ${i}`,
        status: i % 2 === 0 ? 'Active' : 'Inactive'
    }));
};

describe('DataGridRenderer Performance', () => {
    it('renders only visible rows with virtualization', () => {
        const data = generateData(1000);
        render(<DataGridRenderer data={data} />);

        // Expected visible count: 600 / 40 = 15.
        // We verify that we have ~15 items, not 1000.

        expect(screen.getByText('Item 0')).toBeTruthy();
        expect(screen.getByText('Item 14')).toBeTruthy();

        // Item 100 should NOT be rendered by our mock logic
        expect(screen.queryByText('Item 100')).toBeNull();

        // Count rows
        const renderedItems = screen.getAllByText(/^Item \d+$/);
        expect(renderedItems.length).toBeLessThan(50);
        expect(renderedItems.length).toBeGreaterThan(0);

        console.log(`Verified virtualization: rendered ${renderedItems.length} items.`);
    });
});

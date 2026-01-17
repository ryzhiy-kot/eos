import React from 'react';

interface DataGridRendererProps {
    data: any[];
}

const DataGridRenderer: React.FC<DataGridRendererProps> = ({ data }) => {
    if (!data || data.length === 0) return <div className="p-4 text-neutral-500">No data available</div>;

    const headers = Object.keys(data[0]);

    return (
        <div className="h-full w-full overflow-auto bg-neutral-900">
            <table className="min-w-full text-left text-xs font-mono">
                <thead className="sticky top-0 bg-neutral-800 text-neutral-300">
                    <tr>
                        {headers.map((header) => (
                            <th key={header} className="px-4 py-2 border-b border-neutral-700 font-medium uppercase tracking-wider">
                                {header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-neutral-800 text-neutral-400">
                    {data.map((row, idx) => (
                        <tr key={idx} className="hover:bg-white/5 transition-colors">
                            {headers.map((header) => (
                                <td key={`${idx}-${header}`} className="px-4 py-2 whitespace-nowrap">
                                    {typeof row[header] === 'object' ? JSON.stringify(row[header]) : String(row[header])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default DataGridRenderer;

import React, { useState } from 'react';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { X, Search, Terminal, ArrowRight } from 'lucide-react';

const commands = [
    { cmd: '/load [file]', desc: 'Load a file (PDF, CSV, JSON) into a new pane.' },
    { cmd: '/grid [1|2|4|9]', desc: 'Set the number of visible panes.' },
    { cmd: '/focus [PaneID]', desc: 'Switch focus to a specific pane.' },
    { cmd: '/swap [P1] [P2]', desc: 'Swap the positions of two panes.' },
    { cmd: '/close [PaneID]', desc: 'Archive a pane (alias for /hide).' },
    { cmd: '/ls', desc: 'Open the Archive Gallery (The Shelf).' },
    { cmd: '/undo [PaneID]', desc: 'Undo the last change in a pane.' },
    { cmd: '/redo [PaneID]', desc: 'Redo the last undone change.' },
    { cmd: '/clock [City] [Zone]', desc: 'Add a world clock to the header.' },
    { cmd: '/timer [Sec] [Label]', desc: 'Start a countdown timer.' },
    { cmd: '/plot [P1] "prompt"', desc: 'Generate a chart from data.' },
    { cmd: '/run [P1] "code"', desc: 'Execute code against pane data.' },
    { cmd: '/diff [P1],[P2]', desc: 'Compare two panes.' },
];

const HelpOverlay: React.FC = () => {
    const { isHelpOpen, toggleHelpOverlay, setPendingCommand } = useWorkspaceStore();
    const [search, setSearch] = useState('');

    if (!isHelpOpen) return null;

    const filteredCommands = commands.filter(c =>
        c.cmd.toLowerCase().includes(search.toLowerCase()) ||
        c.desc.toLowerCase().includes(search.toLowerCase())
    );

    const handleSelect = (cmdExample: string) => {
        // Extract just the command verb or base example
        const baseCmd = cmdExample.split(' ')[0];
        setPendingCommand(`${baseCmd} `);
        toggleHelpOverlay(false);
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-md flex flex-col p-8 animate-in fade-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between mb-8 border-b border-neutral-800 pb-4">
                <div className="flex items-center space-x-4">
                    <h2 className="text-2xl font-mono font-bold text-white">COMMAND CENTER (HELP)</h2>
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs font-mono border border-blue-500/30">v1.0</span>
                </div>
                <button onClick={() => toggleHelpOverlay(false)} className="text-neutral-500 hover:text-white transition-colors">
                    <X size={32} />
                </button>
            </div>

            {/* Search */}
            <div className="mb-8 w-full max-w-2xl mx-auto relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-blue-500 transition-colors" />
                <input
                    type="text"
                    placeholder="Search commands..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-neutral-900 border border-neutral-800 rounded-full py-3 pl-12 pr-4 text-white font-mono focus:border-blue-500 outline-none transition-colors"
                    autoFocus
                />
            </div>

            {/* Command Grid */}
            <div className="flex-1 overflow-y-auto w-full max-w-4xl mx-auto">
                <div className="grid grid-cols-1 gap-2">
                    {filteredCommands.map((c, i) => (
                        <div
                            key={i}
                            onClick={() => handleSelect(c.cmd)}
                            className="group flex items-center justify-between p-4 rounded-lg border border-neutral-800 hover:border-blue-500 hover:bg-neutral-900 cursor-pointer transition-all"
                        >
                            <div className="flex items-center space-x-4">
                                <div className="p-2 bg-neutral-800 rounded text-neutral-400 group-hover:text-blue-400 transition-colors">
                                    <Terminal size={20} />
                                </div>
                                <div>
                                    <div className="font-mono font-bold text-lg text-white group-hover:text-blue-400 transition-colors">
                                        {c.cmd}
                                    </div>
                                    <div className="text-neutral-500 text-sm">
                                        {c.desc}
                                    </div>
                                </div>
                            </div>
                            <ArrowRight className="text-neutral-700 group-hover:text-white transition-colors" />
                        </div>
                    ))}

                    {filteredCommands.length === 0 && (
                        <div className="text-center text-neutral-500 py-12">
                            No commands found matching "{search}"
                        </div>
                    )}
                </div>
            </div>

            <div className="mt-8 text-center text-neutral-600 font-mono text-xs">
                Press [ESC] to close • Click a command to use it
            </div>
        </div>
    );
};

export default HelpOverlay;

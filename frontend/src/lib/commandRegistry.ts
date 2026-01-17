export interface CommandParameter {
    name: string;
    description: string;
    required: boolean;
    type?: 'string' | 'number' | 'paneId' | 'file';
}

export interface CommandContext {
    sourceId?: string;
    targetId?: string;
    focusedPaneId: string | null;
    [key: string]: any;
}

export interface CommandEntry {
    name: string;
    description: string;
    parameters?: CommandParameter[];
    example?: string;
    category?: 'system' | 'pane' | 'utility' | 'data';
    handler?: (args: string[], context: CommandContext) => boolean | Promise<boolean>;
}

/**
 * Utility to format a command entry into a displayable usage string.
 * e.g., /grid [1|2|4|9]
 */
export const formatCommandUsage = (entry: CommandEntry): string => {
    if (entry.example) return entry.example;

    let usage = `/${entry.name}`;
    if (entry.parameters) {
        entry.parameters.forEach(p => {
            const paramStr = p.required ? `<${p.name}>` : `[${p.name}]`;
            usage += ` ${paramStr}`;
        });
    }
    return usage;
};

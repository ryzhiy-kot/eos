import { CommandName } from './commandBus';

export interface CommandParameter {
    name: string;
    description: string;
    required: boolean;
    type?: 'string' | 'number' | 'paneId' | 'file';
}


export interface CommandEntry {
    name: CommandName;
    description: string;
    parameters?: CommandParameter[];
    example?: string;
    shortcut?: string; // e.g., 'ctrl+/' or 'alt+l'
    category?: 'system' | 'pane' | 'utility' | 'data';
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

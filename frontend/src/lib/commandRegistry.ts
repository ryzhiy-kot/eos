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

import { CommandName } from './commandBus';
import { CommandParameterType, CommandCategory } from '@/types/constants';

export interface CommandParameter {
    name: string;
    description: string;
    required: boolean;
    type?: CommandParameterType;
}


export interface CommandEntry {
    name: CommandName;
    description: string;
    parameters?: CommandParameter[];
    example?: string;
    shortcut?: string; // e.g., 'ctrl+/' or 'alt+l'
    category?: CommandCategory;
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

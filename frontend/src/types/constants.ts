/**
 * PROJECT: MONAD
 * AUTHOR: Kyrylo Yatsenko
 * YEAR: 2026
 * * COPYRIGHT NOTICE:
 * © 2026 Kyrylo Yatsenko. All rights reserved.
 */

export const PaneType = {
    CHAT: 'chat',
    DATA: 'data',
    DOC: 'doc',
    VISUAL: 'visual',
    CODE: 'code',
    EMPTY: 'empty'
} as const;
export type PaneType = typeof PaneType[keyof typeof PaneType];

export const ChatRole = {
    USER: 'user',
    ASSISTANT: 'assistant',
    SYSTEM: 'system'
} as const;
export type ChatRole = typeof ChatRole[keyof typeof ChatRole];

export const MutationOriginType = {
    ADHOC_COMMAND: 'adhoc_command',
    CHAT_INFERENCE: 'chat_inference',
    MANUAL_EDIT: 'manual_edit'
} as const;
export type MutationOriginType = typeof MutationOriginType[keyof typeof MutationOriginType];

export const MutationStatus = {
    GHOST: 'ghost',
    COMMITTED: 'committed',
    REVERTED: 'reverted'
} as const;
export type MutationStatus = typeof MutationStatus[keyof typeof MutationStatus];

export const NotificationType = {
    ERROR: 'error',
    SUCCESS: 'success',
    INFO: 'info'
} as const;
export type NotificationType = typeof NotificationType[keyof typeof NotificationType];

export const ConnectionStatus = {
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    ERROR: 'error'
} as const;
export type ConnectionStatus = typeof ConnectionStatus[keyof typeof ConnectionStatus];

export const OverlayType = {
    SHELF: 'shelf',
    HELP: 'help',
    LOOKUP: 'lookup',
    ARTIFACT_PICKER: 'artifact_picker'
} as const;
export type OverlayType = typeof OverlayType[keyof typeof OverlayType] | null;

export const ExecutionType = {
    COMMAND: 'command',
    CHAT: 'chat'
} as const;
export type ExecutionType = typeof ExecutionType[keyof typeof ExecutionType];

export const CommandParameterType = {
    STRING: 'string',
    NUMBER: 'number',
    PANE_ID: 'paneId',
    FILE: 'file'
} as const;
export type CommandParameterType = typeof CommandParameterType[keyof typeof CommandParameterType];

export const CommandCategory = {
    SYSTEM: 'system',
    PANE: 'pane',
    UTILITY: 'utility',
    DATA: 'data'
} as const;
export type CommandCategory = typeof CommandCategory[keyof typeof CommandCategory];

export const ResourceType = {
    PANE: 'pane',
    ARTIFACT: 'artifact',
    FILE: 'file'
} as const;
export type ResourceType = typeof ResourceType[keyof typeof ResourceType];

export const LayoutDensity = {
    SINGLE: 1,
    DUAL: 2,
    QUAD: 4,
    GRID: 9
} as const;
export type LayoutDensity = typeof LayoutDensity[keyof typeof LayoutDensity];

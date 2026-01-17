import { PaneType } from '../store/workspaceStore';

// Types mimicking the backend response
type BackendResponse = {
    type: PaneType;
    title: string;
    content: any;
};

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockExecute = async (
    verb: string,
    sourceId?: string,
    action?: string,
    targetId?: string
): Promise<BackendResponse> => {
    await delay(600); // Simulate network latency

    switch (verb) {
        case 'load':
            // Logic moved to frontend, but if called via backend fallback:
            return {
                type: 'data',
                title: `Data: ${action || 'Untitled'}`,
                content: [
                    { id: 1, name: 'Alpha', value: 100 },
                    { id: 2, name: 'Beta', value: 200 },
                    { id: 3, name: 'Gamma', value: 150 },
                ]
            };

        case 'plot':
            return {
                type: 'visual',
                title: `Plot: ${action || 'Analysis'}`,
                content: { chartType: 'bar', data: [100, 200, 150], note: 'Mock visualization' }
            };

        case 'ask':
        case 'chat':
            return {
                type: 'chat',
                title: 'Chat Assistant',
                content: [{ role: 'assistant', content: `I processed your request: "${action}"\n\nIs there anything else I can help you with regarding **${sourceId || 'this context'}**?` }]
            };

        case 'diff':
            return {
                type: 'code',
                title: `Diff: ${sourceId} vs ...`,
                content: `--- ${sourceId}\n+++ ${targetId || 'Comparison'}\n@@ -1,3 +1,3 @@\n- Old Value\n+ New Value\n Unchanged line`
            };

        case 'run':
            return {
                type: 'code',
                title: 'Execution Output',
                content: `> Executing python script...\n> [DETAILS] Processing data from ${sourceId}\n> Done.\n\nResult: 42`
            };

        case 'tab':
            return {
                type: 'data',
                title: 'Extracted Table',
                content: [
                    { Row: 1, ColA: 'Data 1', ColB: 'Data 2' },
                    { Row: 2, ColA: 'Data 3', ColB: 'Data 4' }
                ]
            };

        case 'summarize':
            return {
                type: 'chat',
                title: `Summary: ${sourceId || 'Context'}`,
                content: [{ role: 'assistant', content: `**Summary of ${sourceId || 'context'}**:\n\nBased on the analysis, the key indicators suggest a positive trend with 15% growth in efficiency. Risk factors remain low, but monitoring of ${targetId || 'external variables'} is recommended.\n\n*   **Key Point 1**: Optimization successful.\n*   **Key Point 2**: Latency reduced by 25%.\n*   **Action Item**: Proceed with Phase 2 deployment.` }]
            };

        default:
            return {
                type: 'chat',
                title: 'Default',
                content: [{ role: 'system', content: `Unknown command: ${verb}` }]
            };
    }
};

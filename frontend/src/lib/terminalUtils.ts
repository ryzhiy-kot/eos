export const generatePaneId = (panes: Record<string, any>) => {
    const numbers = Object.keys(panes)
        .map(id => parseInt(id.replace(/^P/, '')))
        .filter(n => !isNaN(n));
    const maxId = numbers.length > 0 ? Math.max(...numbers) : 0;
    return `P${maxId + 1}`;
};

/**
 * Parses duration expressions like "20m", "50s", "20 minutes", etc.
 * Default unit is minutes if none provided.
 */
export const parseDurationExpression = (inputArgs: string[]): { seconds: number, labelStartIdx: number } => {
    let totalSeconds = 0;
    let ptr = 0;
    let hasTime = false;

    while (ptr < inputArgs.length) {
        const arg = inputArgs[ptr].toLowerCase();

        // Check for "20m", "50s" format
        const combinedMatch = arg.match(/^(\d+)([ms])$/);
        if (combinedMatch) {
            const val = parseInt(combinedMatch[1]);
            const unit = combinedMatch[2];
            totalSeconds += unit === 'm' ? val * 60 : val;
            hasTime = true;
            ptr++;
            continue;
        }

        // Check for pure number
        if (/^\d+$/.test(arg)) {
            const val = parseInt(arg);
            // Look ahead for unit
            if (ptr + 1 < inputArgs.length) {
                const next = inputArgs[ptr + 1].toLowerCase();
                const minutesUnits = ['m', 'min', 'mins', 'minute', 'minutes'];
                const secondsUnits = ['s', 'sec', 'secs', 'second', 'seconds'];

                if (minutesUnits.includes(next)) {
                    totalSeconds += val * 60;
                    hasTime = true;
                    ptr += 2;
                    continue;
                }
                if (secondsUnits.includes(next)) {
                    totalSeconds += val;
                    hasTime = true;
                    ptr += 2;
                    continue;
                }
            }

            // No explicit unit following
            if (!hasTime) {
                // First number encountered, default to minutes as per requirement
                totalSeconds += val * 60;
                hasTime = true;
                ptr++;
            } else {
                // Subsequent number, assume seconds (e.g., "20 minutes 50")
                totalSeconds += val;
                ptr++;
            }
            continue;
        }

        // Hit something else (label starts)
        break;
    }

    return { seconds: totalSeconds, labelStartIdx: ptr };
};

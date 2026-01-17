import { useEffect, useCallback } from 'react';
import { commandBus, CommandName, CommandPayload } from '../lib/commandBus';

export const useCommandHandler = (
    name: CommandName,
    handler: (payload: CommandPayload) => void | boolean | Promise<void | boolean>
) => {
    const stableHandler = useCallback(handler, [handler]);

    useEffect(() => {
        return commandBus.subscribe(name, stableHandler);
    }, [name, stableHandler]);
};

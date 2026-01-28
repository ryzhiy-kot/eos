import { parseCommand } from './frontend/src/lib/parser';
const result = parseCommand('/?', null);
console.log(JSON.stringify(result, null, 2));


/**
 * Reads a file as text using streams to avoid blocking the main thread.
 * It yields execution to the event loop if processing takes longer than the budget.
 *
 * @param file The file to read
 * @returns Promise resolving to the file content as string
 */
export async function readFileTextChunked(file: File): Promise<string> {
    // Fallback for environments without stream() support (unlikely in modern browsers)
    if (!file.stream) {
        return file.text();
    }

    const stream = file.stream();
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    const chunks: string[] = [];

    let lastYield = performance.now();
    const YIELD_INTERVAL_MS = 16; // Yield every ~1 frame (16ms) to keep UI responsive

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            chunks.push(decoder.decode(value, { stream: true }));

            const now = performance.now();
            if (now - lastYield > YIELD_INTERVAL_MS) {
                await new Promise(resolve => setTimeout(resolve, 0));
                lastYield = performance.now();
            }
        }
        // Flush any remaining bytes
        chunks.push(decoder.decode());
    } catch (err) {
        // If streaming fails, fallback to standard text() read
        console.warn('Stream reading failed, falling back to file.text()', err);
        return file.text();
    } finally {
        reader.releaseLock();
    }

    return chunks.join('');
}

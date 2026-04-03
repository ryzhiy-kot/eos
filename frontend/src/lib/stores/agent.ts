import { writable } from "svelte/store";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  charts: any[];
  tables: any[];
  timestamp: Date;
}

export const messages = writable<ChatMessage[]>([]);
export const isAgentTyping = writable(false);
export const currentConversationId = writable<string | null>(null);
export const conversations = writable<any[]>([]);

export function addUserMessage(content: string) {
  messages.update((msgs) => [
    ...msgs,
    {
      id: crypto.randomUUID(),
      role: "user",
      content,
      charts: [],
      tables: [],
      timestamp: new Date(),
    },
  ]);
}

export function addAssistantMessage(content: string, charts: any[] = [], tables: any[] = []) {
  messages.update((msgs) => [
    ...msgs,
    {
      id: crypto.randomUUID(),
      role: "assistant",
      content,
      charts,
      tables,
      timestamp: new Date(),
    },
  ]);
}

export function clearMessages() {
  messages.set([]);
}

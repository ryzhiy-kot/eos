import { writable, get } from "svelte/store";
import { api } from "$lib/api/client";

export interface ArtifactPosition {
  x: number;
  y: number;
  width: number;
  height: number;
  visible: boolean;
}

export interface Workspace {
  id: string;
  user_id: string;
  name: string;
  artifact_positions: Record<string, ArtifactPosition>;
  created_at: Date;
  updated_at: Date;
}

export const workspaces = writable<Workspace[]>([]);
export const currentWorkspaceId = writable<string | null>(null);
export const artifactPositions = writable<Record<string, ArtifactPosition>>({});

export async function fetchWorkspaces() {
  try {
    const result = await api.get<{ workspaces: Workspace[] }>("/workspaces/");
    workspaces.set(result.workspaces.map((w) => ({
      ...w,
      created_at: new Date(w.created_at),
      updated_at: new Date(w.updated_at),
    })));
    return result.workspaces;
  } catch (e) {
    console.error("Failed to fetch workspaces:", e);
    return [];
  }
}

export async function createWorkspace(name: string): Promise<Workspace | null> {
  try {
    const workspace = await api.post<Workspace>("/workspaces/", { name });
    const ws: Workspace = {
      ...workspace,
      created_at: new Date(workspace.created_at),
      updated_at: new Date(workspace.updated_at),
    };
    workspaces.update((list) => [...list, ws]);
    return ws;
  } catch (e) {
    console.error("Failed to create workspace:", e);
    return null;
  }
}

export async function updateArtifactPositions(
  workspaceId: string,
  positions: Record<string, ArtifactPosition>
) {
  try {
    const workspace = await api.put<Workspace>(`/workspaces/${workspaceId}`, {
      artifact_positions: positions,
    });
    artifactPositions.set(positions);
    workspaces.update((list) =>
      list.map((w) => (w.id === workspaceId ? {
        ...w,
        artifact_positions: positions,
        updated_at: new Date(workspace.updated_at),
      } : w))
    );
  } catch (e) {
    console.error("Failed to update workspace:", e);
  }
}

export async function selectWorkspace(workspaceId: string | null) {
  currentWorkspaceId.set(workspaceId);
  if (workspaceId) {
    const ws = get(workspaces).find((w) => w.id === workspaceId);
    if (ws) {
      artifactPositions.set(ws.artifact_positions);
    }
  } else {
    artifactPositions.set({});
  }
}

export async function deleteWorkspace(workspaceId: string) {
  try {
    await api.post(`/workspaces/${workspaceId}`, { method: "DELETE" } as any);
    workspaces.update((list) => list.filter((w) => w.id !== workspaceId));
  } catch (e) {
    console.error("Failed to delete workspace:", e);
  }
}
import { createContext, useContext } from 'react';
import type { AgentDraft, DemoState, Role } from './types';

export type ModalState =
  | { type: 'simulation' }
  | { type: 'call' | 'contact' | 'appointment' | 'job' | 'document'; id: string }
  | null;
export type Mutation = (
  operation: (state: DemoState, role: Role) => DemoState,
  message: string,
) => string | undefined;
export interface Workspace {
  state: DemoState;
  role: Role;
  query: string;
  setQuery: (query: string) => void;
  mutate: Mutation;
  open: (modal: ModalState) => void;
  agentEditor: AgentDraft;
  setAgentEditor: (draft: AgentDraft) => void;
}
export const WorkspaceContext = createContext<Workspace | null>(null);
export function useWorkspace(): Workspace {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error('Workspace unavailable');
  return context;
}

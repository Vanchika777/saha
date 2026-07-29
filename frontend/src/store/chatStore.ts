import { create } from 'zustand';
import type { ChatMessage, ChatSession } from '../types';

interface ChatState {
  currentSession: ChatSession | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  activeStreamToken: string;
  setCurrentSession: (session: ChatSession | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  appendStreamToken: (token: string) => void;
  clearStreamToken: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  currentSession: null,
  messages: [],
  isStreaming: false,
  activeStreamToken: '',

  setCurrentSession: (session) =>
    set({
      currentSession: session,
      messages: session ? session.messages : [],
    }),

  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  setIsStreaming: (isStreaming) => set({ isStreaming }),
  appendStreamToken: (token) =>
    set((state) => ({ activeStreamToken: state.activeStreamToken + token })),
  clearStreamToken: () => set({ activeStreamToken: '' }),
}));

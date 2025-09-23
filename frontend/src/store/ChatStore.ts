// store/chatStore.ts
import { create } from "zustand";

export const useChatStore = create<{
  initialMessage: string | null;
  setInitialMessage: (msg: string | null) => void;
}>((set) => ({
  initialMessage: null,
  setInitialMessage: (msg) => set({ initialMessage: msg }),
}));
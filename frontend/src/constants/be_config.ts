// BE Configs
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
export const ENDPOINTS = {
  CHAT: "/api/chat/invoke", // query chat
  CHAT_CREATE: "/api/chat/create", // create chat
  CHAT_HISTORY: "/api/chat/history", // query chat
  CHAT_LISTS: "/api/chat/lists", // list chats
};
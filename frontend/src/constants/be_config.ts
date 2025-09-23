// BE Configs
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
export const ENDPOINTS = {
  REQUEST_MAGIC_LINK: "/api/auth/magic-link/send",
  VERIFY_MAGIC_LINK: "/api/auth/magic-link/verify", // generate token
  CHECK_SESSION: "/api/auth/session", // check jwt
  CHAT: "/api/chat/invoke", // query chat
  CHAT_CREATE: "/api/chat/create", // create chat
  CHAT_HISTORY: "/api/chat/history", // query chat
  CHAT_LISTS: "/api/chat/lists", // list chats
};
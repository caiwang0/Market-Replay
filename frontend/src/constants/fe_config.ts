// BE Configs
const PREFIX = process.env.NEXT_PUBLIC_PREFIX || "";
export const PATHS = {
  CHAT_HOME: PREFIX + "/",
  CHAT_SESSION: PREFIX + "/chat/:chat_uuid",
};
export const PUBLIC_PATHS = [PATHS.CHAT_HOME, PATHS.CHAT_SESSION] 
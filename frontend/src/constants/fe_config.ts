// BE Configs
export const PATHS = {
  CHAT_HOME: process.env.NEXT_PUBLIC_PREFIX+"/",
  LOGIN: process.env.NEXT_PUBLIC_PREFIX+"/login",
  VERIFY: process.env.NEXT_PUBLIC_PREFIX+"/verify",
  WAITING: process.env.NEXT_PUBLIC_PREFIX+"/waiting",
  CHAT_SESSION: process.env.NEXT_PUBLIC_PREFIX+"/chat/:chat_uuid",
};
export const PUBLIC_PATHS = [PATHS.LOGIN, PATHS.VERIFY, PATHS.WAITING] // path that doesn't require auth
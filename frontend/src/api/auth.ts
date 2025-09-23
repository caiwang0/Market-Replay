import { API_BASE_URL, ENDPOINTS } from "@/constants/be_config";

export const requestMagicLink = async (email: string) => {
  const res = await fetch(`${API_BASE_URL}${ENDPOINTS.REQUEST_MAGIC_LINK}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email }),
  });
  return res;
};

export const verifyMagicLink = async (email: string, verifyToken: string) => {
  const res = await fetch(`${API_BASE_URL}${ENDPOINTS.VERIFY_MAGIC_LINK}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, verifyToken }),
  });
  return res;
};

export const checkSession = async () => {
  const res = await fetch(`${API_BASE_URL}${ENDPOINTS.CHECK_SESSION}`, {
    method: "GET",
    credentials: "include",
  });
  return res;
};
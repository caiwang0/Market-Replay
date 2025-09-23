import { API_BASE_URL, ENDPOINTS } from "@/constants/be_config";

export const chatInvoke = async (text: string, chatUuid?: string) => {
    const res = await fetch(`${API_BASE_URL}${ENDPOINTS.CHAT}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Important for authentication
        body: JSON.stringify({
            query: text,
            chat_uuid: chatUuid || null
        }),
    });
    return res;
};

export const chatCreate = async (text: string) => {
    const res = await fetch(`${API_BASE_URL}${ENDPOINTS.CHAT_CREATE}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Important for authentication
        body: JSON.stringify({
            query: text
        }),
    });
    return res;
};

export const chatHistory = async (chat_uuid: string, offset: number, limit: number) => {
    const res = await fetch(`${API_BASE_URL}${ENDPOINTS.CHAT_HISTORY}?chat_uuid=${chat_uuid}&offset=${offset}&limit=${limit}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Important for authentication
    });
    return res;
};


export const chatLists = async () => {
    const res = await fetch(`${API_BASE_URL}${ENDPOINTS.CHAT_LISTS}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Important for authentication
    });
    return res;
};
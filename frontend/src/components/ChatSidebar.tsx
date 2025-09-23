"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PATHS } from "@/constants/fe_config";
import { chatLists } from "@/api/chat";

type ChatSidebarProps = {
  isOpen: boolean;
  onClose?: () => void;
};

export default function ChatSidebar({ isOpen, onClose }: ChatSidebarProps) {
  const [chatList, setChatList] = useState<{ chat_uuid: string; title?: string }[]>([]);
  const params = useParams();
  const router = useRouter();
  const activeChatId = String(params?.chat_uuid || "");

  useEffect(() => {
      async function loadChats() {
        const res = await chatLists();
        const data = await res.json();
        setChatList(data.chats || []);
      }
      loadChats();
    }, []);

  return (
    <div
      className={`fixed top-0 left-0 h-full w-64 bg-gray-900 text-white shadow-lg z-40 transform transition-transform duration-300 ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <span className="font-bold text-lg">Chats</span>
            <button
                onClick={() => {
                if (onClose) onClose();
                router.push(PATHS.CHAT_HOME); // Redirect to home/new chat
                }}
                className="text-sm text-blue-400 hover:underline"
            >
                + New Chat
            </button>
        </div>
      <ul className="p-4 space-y-2 overflow-y-auto">
        {chatList.map((chat) => {
          const isActive = String(chat.chat_uuid) === activeChatId;
          return (
            <li key={chat.chat_uuid}>
              <button
                onClick={() => {
                  if (onClose) onClose();
                  router.push(PATHS.CHAT_SESSION.replace(":chat_uuid", chat.chat_uuid));
                }}
                className={`w-full text-left px-2 py-1 rounded border-l-4 ${
                  isActive
                    ? "border-blue-400 bg-blue-600 font-semibold"
                    : "border-transparent hover:bg-gray-700"
                }`}
              >
                {chat.title || `Chat ${chat.chat_uuid.slice(0, 5)}`}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import TextArea from "@/components/TextArea";
import MenuIcon from "@/components/MenuIcon";
import ChatSidebar from "@/components/ChatSidebar";
import { ChatOutput } from "@/types/types";
import { PATHS } from "@/constants/fe_config";
import { chatCreate } from "@/api/chat";
import { useChatStore } from "@/store/ChatStore";

export default function Home() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [outputs, setOutputs] = useState<ChatOutput[]>([]);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  

  // Handle first message submission
  const handleFirstMessage = async (text: string) => {
    try {
      // Create a new chat_id via API
      const res = await chatCreate(text);
      const data = await res.json();
      const newChatId = data.chat_uuid;
      // const newChatId = 4;

      useChatStore.getState().setInitialMessage(text);

      // Redirect to new chat page, optionally with message as query param
      router.push(PATHS.CHAT_SESSION.replace(":chat_uuid", newChatId));
    } catch (err) {
      console.error("Failed to start chat", err);
    }
  };
  
  return (
    <div
      ref={containerRef}
      className={`container pt-10 pb-32 min-h-screen ${
        outputs.length === 0 && "flex items-center justify-center"
      }`}
    >
      {/* Sidebar */}
      <button
        className={`fixed top-5 z-50 bg-gray-800 p-2 rounded-md text-white hover:bg-gray-700 transition-all duration-300
        ${isSidebarOpen ? "left-64" : "left-5"}`}
        onClick={() => setSidebarOpen(!isSidebarOpen)}
        aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
      >
        {isSidebarOpen ? (
          // Close icon (X)
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <MenuIcon />
        )}
      </button>
      
      <ChatSidebar isOpen={isSidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="w-full">
        <h1 className="text-4xl text-center mb-5">
          What do you want to know?
        </h1>

        <TextArea
          setIsGenerating={setIsGenerating}
          isGenerating={isGenerating}
          outputs={outputs}
          setOutputs={setOutputs}
          onFirstSubmit={handleFirstMessage} // <- Custom prop
          chatUuid=""
        />
      </div>
    </div>
  );
}
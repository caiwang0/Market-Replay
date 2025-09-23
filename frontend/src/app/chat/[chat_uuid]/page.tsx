"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useParams } from 'next/navigation';
import Output from "@/components/Output";
import TextArea from "@/components/TextArea";
import MenuIcon from "@/components/MenuIcon";
import ChatSidebar from "@/components/ChatSidebar";
import { PATHS } from "@/constants/fe_config";
import { type ChatOutput } from "@/types/types";
import { useChatStore } from "@/store/ChatStore";
import { chatHistory, chatLists } from "@/api/chat";


export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const textAreaRef = useRef<{ sendMessage: (text: string) => void }>(null);
  const [outputs, setOutputs] = useState<ChatOutput[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const isLoadingMoreRef = useRef(false);
  const [history, setHistory] = useState<ChatOutput[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [hasScrolledInitially, setHasScrolledInitially] = useState(false);
  const initialMessage = useChatStore((state) => state.initialMessage);
  const clearInitialMessage = useChatStore((state) => state.setInitialMessage);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [chatList, setChatList] = useState<{ chat_uuid: string; title?: string }[]>([]);  
  const chatUuid = params?.chat_uuid as string;

  // Fetch initial chat history
  useEffect(() => {
    fetchHistory(0);
  }, []);
  async function fetchHistory(currentOffset: number) {
    setIsLoadingMore(true);
    isLoadingMoreRef.current = true;
    try {
      const prevScrollTop = window.scrollY;
      const prevHeight = document.body.scrollHeight;

      // fetch chat history from API
      const res = await chatHistory(chatUuid, currentOffset, 20);
      if (res.status !== 200) { // redirect to home if not found
        router.push(PATHS.CHAT_HOME);
        return;
      }
      const data = await res.json();

      if (currentOffset === 0) {
        setHistory(data.messages);
      } else {
        setHistory(prev => [...data.messages, ...prev]);

      // Wait for DOM to update
      requestAnimationFrame(() => {
        const newHeight = document.body.scrollHeight;
        const heightDiff = newHeight - prevHeight;
        window.scrollTo({ top: prevScrollTop + heightDiff - 1100});
      });
    }

      setHasMore(data.has_more);
      setOffset(currentOffset + data.messages.length);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setIsLoadingMore(false);
      isLoadingMoreRef.current = false;
    }
  }

  // Handle first message submission (when redirecting from home page)
  useEffect(() => {
    if (initialMessage && outputs.length === 0 && textAreaRef.current) {
      textAreaRef.current.sendMessage(initialMessage);
      clearInitialMessage(null);
    }
  }, [initialMessage]);

  // Scroll to bottom ONLY on first load (offset === 0)
  useEffect(() => {
    if (!hasScrolledInitially && history.length > 0) {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "auto" });
      setHasScrolledInitially(true); // Set flag to true after first scroll
    }
  }, [history.length]);

  // Scroll to bottom on new output
  useEffect(() => {
    if (outputs.length > 0) {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }
  }, [outputs.length]);

  // Detect scroll to top
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY < 50 && hasMore && !isLoadingMore && !isLoadingMoreRef.current) {
        fetchHistory(offset);
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [offset, hasMore, isLoadingMore]);

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

      {/* Main Content */}
      <div className="w-full">
      {history.length === 0 && outputs.length === 0 && (
        <h1 className="text-4xl text-center mb-5">
        What do you want to know?
        </h1>
      )}

      {history.map((output, i) => (
        <Output key={`history-${i}`} output={output} />
      ))}

      {isLoadingMore && (
        <div className="text-center text-gray-500 my-4">Loading more...</div>
      )}

      {outputs.map((output, i) => (
        <Output key={`output-${i}`} output={output} />
      ))}

      <TextArea
        ref={textAreaRef}
        setIsGenerating={setIsGenerating}
        isGenerating={isGenerating}
        outputs={outputs}
        setOutputs={setOutputs}
        chatUuid={chatUuid}
      />
      </div>
    </div>
  );
}
"use client";

import { useEffect, useRef, useState } from "react";
import { IncompleteJsonParser } from "incomplete-json-parser";
import { ChatOutput } from "@/types/types";
import { chatInvoke } from "@/api/chat";
import { forwardRef, useImperativeHandle } from "react";

const TextArea = forwardRef(function TextArea(
  {
    setIsGenerating,
    isGenerating,
    setOutputs,
    outputs,
    onFirstSubmit,
    chatUuid
  }: {
    setIsGenerating: React.Dispatch<React.SetStateAction<boolean>>;
    isGenerating: boolean;
    setOutputs: React.Dispatch<React.SetStateAction<ChatOutput[]>>;
    outputs: ChatOutput[];
    onFirstSubmit?: (text: string) => void;
    chatUuid: string;
  },
  ref: React.Ref<{ sendMessage: (text: string) => void }>
) {
  // Parser instance to handle incomplete JSON streaming responses
  const parser = new IncompleteJsonParser();

  const [text, setText] = useState("");
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  // 🆕 Expose sendMessage to parent
  useImperativeHandle(ref, () => ({
    sendMessage,
  }));

  // Handles form submission
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (outputs.length === 0 && onFirstSubmit) {
      onFirstSubmit(text);
    } else {
      sendMessage(text);
    }
    setText("");
  }

  // Sends message to the api and handles both streaming and JSON responses
  const sendMessage = async (text: string) => {
    console.log("🚀 SENDING MESSAGE:", text);
    
    const newOutputs = [
      ...outputs,
      {
        question: text,
        steps: [],
        result: {
          answer: "",
          tools_used: [],
        },
      },
    ];

    setOutputs(newOutputs);
    setIsGenerating(true);

    try {
      const res = await chatInvoke(text, chatUuid);
      console.log("📡 RESPONSE RECEIVED:", res);

      if (!res.ok) {
        console.error("❌ Response not OK:", res.status, res.statusText);
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      // Check content type to determine if it's streaming or JSON
      const contentType = res.headers.get('content-type') || '';
      console.log("🔍 CONTENT TYPE:", contentType);

      if (contentType.includes('text/event-stream')) {
        console.log("📺 PROCESSING AS STREAM...");
        
        // Handle streaming response (original code)
        const data = res.body;
        if (!data) {
          setIsGenerating(false);
          return;
        }

        const reader = data.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let answer = { answer: "", tools_used: [] };
        let currentSteps: { name: string; result: Record<string, string> }[] = [];
        let buffer = "";

        // Process streaming response chunks and parse steps/results
        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          let chunkValue = decoder.decode(value);
          console.log(`📦 CHUNK: ${chunkValue}`);
          if (!chunkValue) continue;

          buffer += chunkValue;

          // Handle different types of steps in the response stream - regular steps and final answer
          if (buffer.includes("</step_name>")) {
            const stepNameMatch = buffer.match(/<step_name>([^<]*)<\/step_name>/);
            if (stepNameMatch) {
              const [_, stepName] = stepNameMatch;
              try {
                if (stepName !== "final_answer") {
                  const fullStepPattern =
                    /<step><step_name>([^<]*)<\/step_name>([^<]*?)(?=<step>|<\/step>|$)/g;
                  const matches = [...buffer.matchAll(fullStepPattern)];

                  for (const match of matches) {
                    const [fullMatch, matchStepName, jsonStr] = match;
                    if (jsonStr) {
                      try {
                        const result = JSON.parse(jsonStr);
                        currentSteps.push({ name: matchStepName, result });
                        buffer = buffer.replace(fullMatch, "");
                      } catch (error) {
                        console.log("Failed to parse step JSON:", error);
                      }
                    }
                  }
                } else {
                  // If it's the final answer step, parse the streaming JSON using incomplete-json-parser
                  const jsonMatch = buffer.match(
                    /(?<=<step><step_name>final_answer<\/step_name>)(.*)/
                  );
                  if (jsonMatch) {
                    const [_, jsonStr] = jsonMatch;
                    parser.write(jsonStr);
                    const result = parser.getObjects();
                    answer = result;
                    parser.reset();
                  }
                }
              } catch (e) {
                console.log("Failed to parse step:", e);
              }
            }
          }

          // Update output with current content and steps
          setOutputs((prevState) => {
            const lastOutput = prevState[prevState.length - 1];
            return [
              ...prevState.slice(0, -1),
              {
                ...lastOutput,
                steps: currentSteps,
                result: answer,
              },
            ];
          });
        }
        
      } else {
        console.log("📄 PROCESSING AS JSON...");
        
        // Handle JSON response (new database-enabled endpoint)
        const responseData = await res.json();
        console.log("✅ JSON RESPONSE DATA:", responseData);
        
        // Update the output with the complete response
        setOutputs((prevState) => {
          const lastOutput = prevState[prevState.length - 1];
          const updatedOutput = {
            ...lastOutput,
            question: responseData.question || text,
            steps: responseData.steps || [],
            result: {
              answer: responseData.result?.answer || responseData.answer || "No response received",
              tools_used: responseData.result?.tools_used || responseData.tools_used || [],
            },
          };
          
          console.log("🎯 UPDATED OUTPUT:", updatedOutput);
          
          return [
            ...prevState.slice(0, -1),
            updatedOutput,
          ];
        });
      }
      
    } catch (error) {
      console.error("❌ SEND MESSAGE ERROR:", error);
      
      // Show error in UI
      setOutputs((prevState) => {
        const lastOutput = prevState[prevState.length - 1];
        return [
          ...prevState.slice(0, -1),
          {
            ...lastOutput,
            result: {
              answer: `Error: ${error}`,
              tools_used: [],
            },
          },
        ];
      });
      
    } finally {
      setIsGenerating(false);
    }
  };

  // Submit form when Enter is pressed (without Shift)
  function submitOnEnter(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.code === "Enter" && !e.shiftKey) {
      submit(e);
    }
  }

  // Dynamically adjust textarea height based on content
  const adjustHeight = () => {
    const textArea = textAreaRef.current;
    if (textArea) {
      textArea.style.height = "auto";
      textArea.style.height = `${textArea.scrollHeight}px`;
    }
  };

  // Adjust height whenever text content changes
  useEffect(() => {
    adjustHeight();
  }, [text]);

  // Add resize event listener to adjust height on window resize
  useEffect(() => {
    const handleResize = () => adjustHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <form
      onSubmit={submit}
      className={`flex gap-3 z-10 ${
        outputs.length > 0 ? "fixed bottom-0 left-0 right-0 container pb-5" : ""
      }`}
    >
      <div className="w-full flex items-center bg-gray-800 rounded border border-gray-600">
        <textarea
          ref={textAreaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => submitOnEnter(e)}
          rows={1}
          className="w-full p-3 bg-transparent min-h-20 focus:outline-none resize-none"
          placeholder="Ask a question..."
        />

        <button
          type="submit"
          disabled={isGenerating || !text}
          className="disabled:bg-gray-500 bg-[#09BDE1] transition-colors w-9 h-9 rounded-full shrink-0 flex items-center justify-center mr-2"
        >
          <ArrowIcon />
        </button>
      </div>
    </form>
  );
});

const ArrowIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="lucide lucide-arrow-right"
  >
    <path d="M5 12h14" />
    <path d="m12 5 7 7-7 7" />
  </svg>
);

export default TextArea;
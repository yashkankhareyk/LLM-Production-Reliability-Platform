"use client";

import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../../services/chatService";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: "user",
      content: input
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(input);

      const aiText = res?.message?.content || "No response";

      const aiMessage = {
        role: "assistant",
        content: aiText
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Error getting response from AI."
        }
      ]);
    }

    setLoading(false);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    inputRef.current?.focus();
  }, [messages]);

  return (
  <div className="flex flex-col h-full bg-gradient-to-br from-[#0f172a] via-[#020617] to-[#020617] text-white shadow-2xl overflow-hidden">    {/* Header */}
    <div className="p-6 border-b border-slate-800 backdrop-blur-lg bg-black/30">
      <h1 className="text-xl font-semibold tracking-wide flex items-center gap-2">
        🤖 AI Chat
      </h1>
    </div>

    {/* Chat messages */}
    <div className="flex-1 overflow-y-auto px-30 py-6 space-y-6 pb-36">

      {messages.map((msg, index) => (
        <div
          key={index}
          className={`flex ${
            msg.role === "user" ? "justify-end" : "justify-start"
          } animate-fadeIn`}
        >
          <div className="flex items-start gap-3 max-w-2xl">

            {/* AI avatar */}
            {msg.role === "assistant" && (
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center shadow-lg">
                🤖
              </div>
            )}

            {/* Message bubble */}
            <div
              className={`px-5 py-3 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-md transition-all duration-300 hover:scale-[1.02] ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white"
                  : "bg-slate-900/70 border border-slate-700 text-gray-200"
              }`}
            >
              <ReactMarkdown>{msg.content}</ReactMarkdown>

              {/* Copy button */}
              {msg.role === "assistant" && (
                <button
                  className="text-xs text-gray-400 mt-2 hover:text-white transition"
                  onClick={() => navigator.clipboard.writeText(msg.content)}
                >
                  Copy
                </button>
              )}
            </div>

            {/* User avatar */}
            {msg.role === "user" && (
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
                👤
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Loading animation */}
      {loading && (
        <div className="flex items-center gap-3 text-gray-400 animate-pulse">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
            🤖
          </div>
          <div className="bg-slate-900 px-4 py-2 rounded-xl border border-slate-700">
            AI is thinking...
          </div>
        </div>
      )}

      <div ref={bottomRef}></div>
    </div>

    {/* Input Area */}
    <div className="border-t border-slate-800 bg-[#020617] p-6 flex justify-center">
      <div className="relative w-full max-w-3xl flex items-end">

        <textarea
      ref={inputRef}
      className="w-full bg-slate-900 border border-slate-700 rounded-2xl py-4 pl-4 pr-12 text-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-400 transition-all overflow-y-auto"
      rows={1}
      style={{ maxHeight: "180px" }}   // ~7 lines
      placeholder="Ask something..."
      value={input}
      onChange={(e) => {
        setInput(e.target.value);

        const textarea = e.target;
        textarea.style.height = "auto";
        textarea.style.height = textarea.scrollHeight + "px";
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      }}
/>

      <button
        onClick={handleSend}
        className="absolute right-3 bottom-3 bg-indigo-600 hover:bg-indigo-500 transition rounded-lg px-3 py-2 flex items-center justify-center"
      >
        <span className="-rotate-90 text-white text-sm">➤</span>
      </button>

      </div>
    </div>

  </div>
);
}
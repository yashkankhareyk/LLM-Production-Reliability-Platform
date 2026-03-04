"use client";

import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../../services/chatService";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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
  }, [messages]);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-gray-50">

      {/* Header */}
      <div className="p-7 border-b bg-white">
        <h1 className="text-lg font-semibold">AI Chat</h1>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 pb-32">

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div className="flex items-start gap-3 max-w-xl">

              {/* Avatar */}
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center">
                  🤖
                </div>
              )}

              {/* Message bubble */}
              <div
                className={`px-4 py-3 rounded-xl text-sm shadow-sm ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white"
                    : "bg-white border"
                }`}
              >
                <ReactMarkdown>{msg.content}</ReactMarkdown>

                {/* Copy button */}
                {msg.role === "assistant" && (
                  <button
                    className="text-xs text-gray-400 mt-2 hover:text-gray-600"
                    onClick={() => navigator.clipboard.writeText(msg.content)}
                  >
                    Copy
                  </button>
                )}
              </div>

              {/* User avatar */}
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">
                  👤
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading animation */}
        {loading && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="animate-pulse">🤖 AI is thinking...</div>
          </div>
        )}

        <div ref={bottomRef}></div>
      </div>

      {/* Input bar */}
      <div className="border-t bg-white p-4 flex gap-3 sticky bottom-0">
        <textarea
          className="flex-1 border rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          rows={2}
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />

        <button
          onClick={handleSend}
          className="bg-blue-500 hover:bg-blue-600 text-white px-6 rounded-lg"
        >
          Send
        </button>
      </div>

    </div>
  );
}
"use client";

import { useState } from "react";
import { mockChatResponse } from "../../mocks/chat.mock";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState<any>(null);

  const handleSend = () => {
    setResponse(mockChatResponse);
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Chat</h2>

      <textarea
        className="w-full p-4 bg-white-800 rounded-lg"
        placeholder="Enter your prompt..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />

      <button
        onClick={handleSend}
        className="mt-4 px-6 py-2 bg-blue-600 rounded-lg"
      >
        Send
      </button>

      {response && (
        <div className="mt-6 bg-white-800 p-4 rounded-lg space-y-2">
          <p>{response.output_text}</p>

          <div className="text-sm text-gray-400">
            <p>Tokens Used: {response.usage.total_tokens}</p>
            <p>Correlation ID: {response.correlation_id}</p>
            <p>Trace ID: {response.trace_id}</p>
          </div>
        </div>
      )}
    </div>
  );
}
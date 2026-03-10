"use client";

import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../../services/chatService";
import ReactMarkdown from "react-markdown";

const IconSend = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const IconCopy = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
);
const IconTrash = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/><path d="M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
);
const IconBot = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <circle cx="12" cy="5" r="2"/><line x1="12" y1="7" x2="12" y2="11"/>
    <line x1="8" y1="15" x2="8" y2="15"/><line x1="16" y1="15" x2="16" y2="15"/>
  </svg>
);
const IconUser = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
);
const IconSparkle = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
  </svg>
);

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState<number | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    if (inputRef.current) { inputRef.current.style.height = "auto"; }
    try {
      const res = await sendChatMessage(input);
      const aiText = res?.message?.content || "No response";
      setMessages((prev) => [...prev, { role: "assistant", content: aiText }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "⚠️ Error getting response from AI." }]);
    }
    setLoading(false);
  };

  const handleCopy = (content: string, idx: number) => {
    navigator.clipboard.writeText(content);
    setCopied(idx);
    setTimeout(() => setCopied(null), 1800);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    inputRef.current?.focus();
  }, [messages]);

  const SUGGESTIONS = ["Summarize my documents", "Find key insights", "Help me analyze data"];

  return (
    <div className="flex flex-col h-full" style={{ background: "var(--bg-base)", transition: "background 0.38s" }}>

      {/* ── Header ── */}
      <div
        className="flex-shrink-0 flex items-center justify-between px-5 sm:px-7 py-3.5"
        style={{
          background: "var(--bg-surface)",
          borderBottom: "1px solid var(--border-subtle)",
          backdropFilter: "blur(16px)",
          transition: "background 0.38s, border-color 0.38s",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: "linear-gradient(135deg, rgba(79,124,255,0.18), rgba(124,95,255,0.18))",
              border: "1px solid rgba(79,124,255,0.25)",
              color: "var(--accent)",
            }}
          >
            <IconBot />
          </div>
          <div>
            <p className="text-sm font-bold leading-tight" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>
              AI Chat
            </p>
            <p className="text-[11px] font-medium flex items-center gap-1.5" style={{ color: loading ? "#ffd43b" : "var(--accent-green)" }}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: loading ? "#ffd43b" : "var(--accent-green)" }} />
              {loading ? "Thinking…" : "Ready"}
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all"
            style={{
              color: "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
              background: "transparent",
              fontFamily: "'Syne', sans-serif",
              cursor: "pointer",
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.color = "var(--accent-red)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,107,107,0.3)";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
              (e.currentTarget as HTMLElement).style.borderColor = "var(--border-subtle)";
            }}
          >
            <IconTrash /> Clear
          </button>
        )}
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 lg:px-16 xl:px-24 py-6 space-y-4">

        {/* Empty state */}
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16 animate-fadeIn">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
              style={{
                background: "linear-gradient(135deg, rgba(79,124,255,0.1), rgba(124,95,255,0.1))",
                border: "1px solid rgba(79,124,255,0.18)",
                boxShadow: "0 0 40px rgba(79,124,255,0.1)",
                color: "var(--accent)",
              }}
            >
              <IconSparkle />
            </div>
            <h2 className="text-lg font-bold mb-2" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>
              Start a conversation
            </h2>
            <p className="text-sm max-w-xs leading-relaxed mb-6" style={{ color: "var(--text-secondary)" }}>
              Ask anything about your documents, request analysis, or explore insights.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-sm">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); inputRef.current?.focus(); }}
                  className="text-xs px-3 py-2 rounded-xl transition-all"
                  style={{
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-secondary)",
                    cursor: "pointer",
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border-glow)";
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border-subtle)";
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Bubbles */}
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex items-end gap-2.5 animate-fadeIn ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            style={{ animationDelay: `${Math.min(index * 0.02, 0.15)}s` }}
          >
            {/* AI avatar */}
            {msg.role === "assistant" && (
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mb-1"
                style={{
                  background: "linear-gradient(135deg, var(--accent), var(--accent-2))",
                  boxShadow: "0 0 14px rgba(79,124,255,0.32)",
                  color: "#fff",
                }}
              >
                <IconBot />
              </div>
            )}

            {/* Bubble */}
            <div className={`max-w-[76%] sm:max-w-[66%] flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}>
              <div
                className="px-4 py-3 text-sm leading-relaxed"
                style={
                  msg.role === "user"
                    ? {
                        background: "linear-gradient(135deg, var(--accent), #6a5aff)",
                        color: "#fff",
                        borderRadius: "18px 18px 4px 18px",
                        boxShadow: "0 4px 18px rgba(79,124,255,0.28)",
                      }
                    : {
                        background: "var(--bg-elevated)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-primary)",
                        borderRadius: "18px 18px 18px 4px",
                        boxShadow: "var(--shadow-card)",
                        transition: "background 0.38s, border-color 0.38s",
                      }
                }
              >
                <ReactMarkdown
                  components={{
                    p:    ({ children }) => <p className="mb-0 last:mb-0">{children}</p>,
                    code: ({ children }) => (
                      <code className="px-1.5 py-0.5 rounded text-xs" style={{ background: "rgba(99,140,255,0.15)", color: "var(--accent)" }}>{children}</code>
                    ),
                    pre: ({ children }) => (
                      <pre className="p-3 rounded-xl text-xs mt-2 overflow-x-auto" style={{ background: "rgba(0,0,0,0.25)", border: "1px solid var(--border-subtle)" }}>{children}</pre>
                    ),
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>

              {msg.role === "assistant" && (
                <button
                  onClick={() => handleCopy(msg.content, index)}
                  className="flex items-center gap-1 px-1.5 py-1 rounded-lg text-[11px] transition-all self-start"
                  style={{
                    color: copied === index ? "var(--accent-green)" : "var(--text-muted)",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    fontFamily: "'Syne', sans-serif",
                  }}
                >
                  <IconCopy />
                  {copied === index ? "Copied!" : "Copy"}
                </button>
              )}
            </div>

            {/* User avatar */}
            {msg.role === "user" && (
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mb-1"
                style={{
                  background: "linear-gradient(135deg, var(--accent), #6a5aff)",
                  boxShadow: "0 0 14px rgba(79,124,255,0.2)",
                  color: "#fff",
                }}
              >
                <IconUser />
              </div>
            )}
          </div>
        ))}

        {/* Loading */}
        {loading && (
          <div className="flex items-end gap-2.5 animate-fadeIn">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background: "linear-gradient(135deg, var(--accent), var(--accent-2))",
                boxShadow: "0 0 14px rgba(79,124,255,0.32)",
                color: "#fff",
              }}
            >
              <IconBot />
            </div>
            <div
              className="px-5 py-3.5 flex items-center gap-2"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "18px 18px 18px 4px",
                transition: "background 0.38s",
              }}
            >
              <div className="thinking-dot" />
              <div className="thinking-dot" />
              <div className="thinking-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input ── */}
      <div
        className="flex-shrink-0 px-4 sm:px-7 py-4"
        style={{
          background: "var(--bg-surface)",
          borderTop: "1px solid var(--border-subtle)",
          backdropFilter: "blur(16px)",
          transition: "background 0.38s, border-color 0.38s",
        }}
      >
        <div className="max-w-3xl mx-auto flex items-end gap-2.5">
          <div
            className="flex-1 rounded-2xl overflow-hidden"
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              transition: "border-color 0.2s, box-shadow 0.2s, background 0.38s",
            }}
            onFocusCapture={e => {
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(79,124,255,0.45)";
              (e.currentTarget as HTMLElement).style.boxShadow = "0 0 0 3px rgba(79,124,255,0.09)";
            }}
            onBlurCapture={e => {
              (e.currentTarget as HTMLElement).style.borderColor = "var(--border-subtle)";
              (e.currentTarget as HTMLElement).style.boxShadow = "none";
            }}
          >
            <textarea
              ref={inputRef}
              className="w-full bg-transparent px-4 py-3.5 text-sm resize-none focus:outline-none"
              style={{ color: "var(--text-primary)", maxHeight: "160px" }}
              rows={1}
              placeholder="Ask something…"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                const ta = e.target;
                ta.style.height = "auto";
                ta.style.height = ta.scrollHeight + "px";
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
              }}
            />
          </div>

          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="btn-primary w-11 h-11 rounded-xl flex items-center justify-center p-0 flex-shrink-0"
            style={{ minWidth: "44px" }}
          >
            <IconSend />
          </button>
        </div>
        <p className="text-center text-[11px] mt-2" style={{ color: "var(--text-muted)", fontFamily: "'Syne', sans-serif" }}>
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
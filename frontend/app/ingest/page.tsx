"use client";

import { useState, useCallback } from "react";
import { uploadFiles } from "../../services/ingestService";

const IconCloud = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 16 12 12 8 16"/>
    <line x1="12" y1="12" x2="12" y2="21"/>
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
  </svg>
);
const IconX = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const IconCheck = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const IconUploadArrow = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);
const IconLightbulb = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/>
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
  </svg>
);

const fileIcon = (name: string) => {
  const ext = name.split(".").pop()?.toLowerCase();
  const style = {
    pdf:  { color: "#ff6b6b", icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> },
    csv:  { color: "#51cf66", icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/></svg> },
    txt:  { color: "#74c0fc", icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg> },
    md:   { color: "#ffd43b", icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> },
    docx: { color: "#a9e34b", icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> },
  } as any;
  return style[ext ?? ""] ?? { color: "#4f7cff", icon: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg> };
};

const fmt = (b: number) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b/1024).toFixed(1)} KB` : `${(b/1048576).toFixed(1)} MB`;

export default function IngestPage() {
  const [files,    setFiles]    = useState<File[]>([]);
  const [loading,  setLoading]  = useState(false);
  const [dragging, setDragging] = useState(false);
  const [success,  setSuccess]  = useState(false);

  const addFiles = useCallback((fl: FileList | null) => {
    if (!fl) return;
    const arr = Array.from(fl);
    setFiles(prev => {
      const seen = new Set(prev.map(f => f.name + f.size));
      return [...prev, ...arr.filter(f => !seen.has(f.name + f.size))];
    });
  }, []);

  const handleUpload = async () => {
    if (!files.length) return;
    setLoading(true); setSuccess(false);
    try {
      await uploadFiles(files);
      setFiles([]); setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch { alert("Upload failed"); }
    setLoading(false);
  };

  const totalSize = files.reduce((a, f) => a + f.size, 0);

  return (
    <div className="min-h-full px-4 sm:px-8 lg:px-12 py-8 max-w-3xl mx-auto">

      {/* Header */}
      <div className="mb-8 animate-fadeIn">
        <h1 className="text-2xl sm:text-3xl font-bold mb-1" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>
          Document Ingestion
        </h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Upload files to build your AI knowledge base
        </p>
      </div>

      {/* Success banner */}
      {success && (
        <div
          className="flex items-center gap-3 px-4 py-3 rounded-2xl mb-5 animate-fadeIn"
          style={{ background: "rgba(81,207,102,0.09)", border: "1px solid rgba(81,207,102,0.25)", color: "var(--accent-green)" }}
        >
          <IconCheck />
          <span className="text-sm font-semibold" style={{ fontFamily: "'Syne', sans-serif" }}>Files uploaded successfully!</span>
        </div>
      )}

      {/* Drop zone */}
      <div
        className={`drop-zone w-full p-10 sm:p-14 text-center mb-5 animate-fadeIn ${dragging ? "drag-over" : ""}`}
        style={{ animationDelay: "0.06s" }}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
        onClick={() => document.getElementById("fileInput")?.click()}
      >
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5"
          style={{
            background: dragging ? "rgba(79,124,255,0.15)" : "rgba(79,124,255,0.07)",
            border: `1px solid ${dragging ? "rgba(79,124,255,0.45)" : "rgba(79,124,255,0.18)"}`,
            color: "var(--accent)",
            boxShadow: dragging ? "0 0 28px rgba(79,124,255,0.2)" : "none",
            transition: "all 0.3s ease",
          }}
        >
          <IconCloud />
        </div>
        <p className="font-bold mb-1.5" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>
          {dragging ? "Release to upload" : "Drag & drop files here"}
        </p>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
          or click to browse from your computer
        </p>
        <p className="text-[11px] font-semibold tracking-widest uppercase" style={{ color: "var(--text-muted)" }}>
          PDF · CSV · TXT · MD · DOCX
        </p>
        <input id="fileInput" type="file" multiple className="hidden" accept=".pdf,.csv,.txt,.md,.docx"
          onChange={e => addFiles(e.target.files)} />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div
          className="rounded-2xl overflow-hidden animate-fadeIn mb-5"
          style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", transition: "background 0.38s, border-color 0.38s" }}
        >
          {/* List header */}
          <div
            className="flex items-center justify-between px-5 py-3"
            style={{ borderBottom: "1px solid var(--border-subtle)" }}
          >
            <p className="text-xs font-bold tracking-wide uppercase" style={{ color: "var(--text-secondary)", fontFamily: "'Syne', sans-serif" }}>
              {files.length} file{files.length !== 1 ? "s" : ""} · {fmt(totalSize)}
            </p>
            <button
              onClick={() => setFiles([])}
              className="text-[11px] transition-colors px-2 py-1 rounded-lg"
              style={{ color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", fontFamily: "'Syne', sans-serif" }}
              onMouseEnter={e => (e.currentTarget.style.color = "var(--accent-red)")}
              onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
            >
              Clear all
            </button>
          </div>

          {/* Items */}
          <div>
            {files.map((file, i) => {
              const { color, icon } = fileIcon(file.name);
              const ext = file.name.split(".").pop()?.toUpperCase();
              return (
                <div
                  key={i}
                  className="flex items-center gap-3 px-5 py-3 group animate-slideIn"
                  style={{
                    borderBottom: i < files.length - 1 ? "1px solid var(--border-subtle)" : "none",
                    animationDelay: `${i * 0.04}s`,
                  }}
                >
                  <span style={{ color, flexShrink: 0 }}>{icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate font-medium" style={{ color: "var(--text-primary)" }}>{file.name}</p>
                    <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{fmt(file.size)}</p>
                  </div>
                  <span
                    className="text-[10px] font-bold uppercase tracking-wider"
                    style={{ color, fontFamily: "'Syne', sans-serif", flexShrink: 0 }}
                  >
                    {ext}
                  </span>
                  <button
                    onClick={() => setFiles(prev => prev.filter((_, j) => j !== i))}
                    className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 opacity-0 group-hover:opacity-100 transition-all"
                    style={{
                      color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer",
                    }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.color = "var(--accent-red)";
                      (e.currentTarget as HTMLElement).style.background = "rgba(255,107,107,0.1)";
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
                      (e.currentTarget as HTMLElement).style.background = "none";
                    }}
                  >
                    <IconX />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Upload button */}
          <div className="p-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
            <button
              onClick={handleUpload}
              disabled={loading}
              className="btn-primary w-full py-3 text-sm flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span
                    className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white"
                    style={{ display: "inline-block", animation: "spinRing 0.7s linear infinite" }}
                  />
                  Uploading…
                </>
              ) : (
                <>
                  <IconUploadArrow />
                  Upload {files.length} file{files.length !== 1 ? "s" : ""}
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Tips */}
      <div
        className="p-4 rounded-2xl animate-fadeIn"
        style={{
          background: "rgba(79,124,255,0.04)",
          border: "1px solid rgba(79,124,255,0.12)",
          animationDelay: "0.12s",
        }}
      >
        <p
          className="text-xs font-bold uppercase tracking-wide mb-2 flex items-center gap-1.5"
          style={{ color: "var(--accent)", fontFamily: "'Syne', sans-serif" }}
        >
          <IconLightbulb /> Tips
        </p>
        <ul className="text-xs space-y-1" style={{ color: "var(--text-secondary)" }}>
          <li>• PDFs and text files work best for knowledge retrieval</li>
          <li>• CSV files are ideal for structured data queries</li>
          <li>• Large files may take a moment to process</li>
        </ul>
      </div>

      {/* Spin animation */}
      <style>{`@keyframes spinRing { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
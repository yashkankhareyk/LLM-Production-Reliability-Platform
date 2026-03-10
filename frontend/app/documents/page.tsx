"use client";

import { useEffect, useState } from "react";
import { getDocuments, deleteDocuments } from "../../services/ingestService";

const IconRefresh = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
  </svg>
);
const IconTrash2 = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/><path d="M14 11v6"/>
    <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
);
const IconUploadLink = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);
const IconInbox = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
  </svg>
);

type FileType = { icon: JSX.Element; color: string; bg: string; border: string; label: string };

const getFileType = (name: string): FileType => {
  const ext = name.split(".").pop()?.toLowerCase();
  const PDF = {
    icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
    color: "#ff6b6b", bg: "rgba(255,107,107,0.1)", border: "rgba(255,107,107,0.22)", label: "PDF",
  };
  const CSV = {
    icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/></svg>,
    color: "#51cf66", bg: "rgba(81,207,102,0.1)", border: "rgba(81,207,102,0.22)", label: "CSV",
  };
  const TXT = {
    icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
    color: "#74c0fc", bg: "rgba(116,192,252,0.1)", border: "rgba(116,192,252,0.22)", label: "TXT",
  };
  const MD = {
    icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    color: "#ffd43b", bg: "rgba(255,212,59,0.1)", border: "rgba(255,212,59,0.22)", label: "MD",
  };
  const DEF = {
    icon: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
    color: "#4f7cff", bg: "rgba(79,124,255,0.1)", border: "rgba(79,124,255,0.22)", label: "FILE",
  };
  return ext === "pdf" ? PDF : ext === "csv" ? CSV : ext === "txt" ? TXT : ext === "md" ? MD : DEF;
};

export default function DocumentsPage() {
  const [files,   setFiles]   = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const data = await getDocuments();
      const docs = data.documents || [];
      const filenames = docs.map((doc: any) => doc.source.split(":")[0]);
      setFiles([...new Set(filenames)] as string[]);
    } catch { console.error("Failed to load documents"); }
    setLoading(false);
  };

  useEffect(() => { loadDocs(); }, []);

  const handleDeleteAll = async () => {
    if (!confirm("Delete all documents?")) return;
    await deleteDocuments();
    loadDocs();
  };

  return (
    <div className="min-h-full px-4 sm:px-8 lg:px-12 py-8 max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 animate-fadeIn">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold mb-1" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>
            Documents
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            {loading ? "Loading…" : `${files.length} file${files.length !== 1 ? "s" : ""} in knowledge base`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadDocs}
            className="flex items-center gap-1.5 text-sm px-3.5 py-2 rounded-xl transition-all"
            style={{
              color: "var(--text-secondary)", background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)", cursor: "pointer",
              fontFamily: "'Syne', sans-serif",
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "var(--text-primary)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)"; }}
          >
            <IconRefresh /> Refresh
          </button>
          {files.length > 0 && (
            <button
              onClick={handleDeleteAll}
              className="flex items-center gap-1.5 text-sm px-3.5 py-2 rounded-xl transition-all"
              style={{
                color: "var(--accent-red)",
                background: "rgba(255,107,107,0.08)",
                border: "1px solid rgba(255,107,107,0.2)",
                cursor: "pointer",
                fontFamily: "'Syne', sans-serif",
              }}
            >
              <IconTrash2 /> Delete All
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      {files.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-6 animate-fadeIn" style={{ animationDelay: "0.05s" }}>
          {[
            { label: "Total",  value: files.length },
            { label: "PDFs",   value: files.filter(f => f.endsWith(".pdf")).length },
            { label: "Others", value: files.filter(f => !f.endsWith(".pdf")).length },
          ].map((s) => (
            <div
              key={s.label}
              className="p-4 rounded-2xl text-center"
              style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", transition: "background 0.38s, border-color 0.38s" }}
            >
              <p className="text-2xl font-bold mb-0.5" style={{ fontFamily: "'Syne', sans-serif", color: "var(--accent)" }}>{s.value}</p>
              <p className="text-[11px] font-semibold tracking-wide uppercase" style={{ color: "var(--text-muted)" }}>{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Skeletons */}
      {loading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 rounded-2xl animate-pulse" style={{ background: "var(--bg-elevated)", animationDelay: `${i * 0.08}s` }} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && files.length === 0 && (
        <div
          className="flex flex-col items-center justify-center py-20 text-center animate-fadeIn rounded-2xl"
          style={{ background: "var(--bg-elevated)", border: "1.5px dashed var(--border-subtle)", transition: "background 0.38s" }}
        >
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
            style={{ background: "rgba(79,124,255,0.08)", border: "1px solid rgba(79,124,255,0.18)", color: "var(--accent)" }}>
            <IconInbox />
          </div>
          <p className="font-bold mb-1.5" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>No documents yet</p>
          <p className="text-sm mb-5" style={{ color: "var(--text-secondary)" }}>Upload files to build your knowledge base</p>
          <a href="/ingest">
            <button className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5">
              <IconUploadLink /> Upload Files
            </button>
          </a>
        </div>
      )}

      {/* File list */}
      {!loading && files.length > 0 && (
        <div className="grid gap-2.5">
          {files.map((file, i) => {
            const ft = getFileType(file);
            return (
              <div
                key={i}
                className="flex items-center gap-3.5 px-4 py-3.5 rounded-2xl animate-fadeIn"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-subtle)",
                  transition: "border-color 0.2s, transform 0.2s, box-shadow 0.2s, background 0.38s",
                  animationDelay: `${i * 0.04}s`,
                  cursor: "default",
                }}
                onMouseEnter={e => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.borderColor = "var(--border-glow)";
                  el.style.transform = "translateY(-1px)";
                  el.style.boxShadow = "var(--shadow-glow)";
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLElement;
                  el.style.borderColor = "var(--border-subtle)";
                  el.style.transform = "none";
                  el.style.boxShadow = "none";
                }}
              >
                {/* Icon */}
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: ft.bg, border: `1px solid ${ft.border}`, color: ft.color }}
                >
                  {ft.icon}
                </div>

                {/* Name */}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate" style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}>
                    {file}
                  </p>
                  <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>Uploaded document</p>
                </div>

                {/* Badge */}
                <span
                  className="text-[10px] font-bold tracking-wider px-2.5 py-1 rounded-lg flex-shrink-0"
                  style={{
                    background: ft.bg, border: `1px solid ${ft.border}`, color: ft.color,
                    fontFamily: "'Syne', sans-serif",
                  }}
                >
                  {ft.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
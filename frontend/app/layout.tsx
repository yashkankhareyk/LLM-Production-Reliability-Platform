"use client";

import "./globals.css";
import Link from "next/link";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

/* ── SVG icon components ── */
const IconChat = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);
const IconUpload = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);
const IconDocuments = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
);
const IconMenu = ({ size = 18 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="3" y1="6"  x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
);
const IconChevronLeft = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
);
const IconChevronRight = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
);
const IconSun = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
);
const IconMoon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
);

const NAV_ITEMS = [
  { href: "/chat",      label: "Chat",           Icon: IconChat },
  { href: "/ingest",    label: "Ingest Files",   Icon: IconUpload },
  { href: "/documents", label: "Documents",      Icon: IconDocuments },
];

/* ── Logo mark ── */
const LogoMark = () => (
  <div
    className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
    style={{
      background: "linear-gradient(135deg, #4f7cff, #7c5fff)",
      boxShadow: "0 0 18px rgba(79,124,255,0.45)",
    }}
  >
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  </div>
);

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [collapsed,   setCollapsed]   = useState(false);
  const [mobileOpen,  setMobileOpen]  = useState(false);
  const [isDark,      setIsDark]      = useState(true);
  const pathname = usePathname();

  /* Apply theme class */
  useEffect(() => {
    document.documentElement.classList.toggle("light", !isDark);
  }, [isDark]);

  /* Close mobile sidebar on route change */
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  /* Close on resize to desktop */
  useEffect(() => {
    const fn = () => { if (window.innerWidth >= 768) setMobileOpen(false); };
    window.addEventListener("resize", fn);
    return () => window.removeEventListener("resize", fn);
  }, []);

  return (
    <html lang="en">
      <body>
        {/* Mobile overlay */}
        {mobileOpen && (
          <div
            className="fixed inset-0 z-40 md:hidden"
            style={{ background: "rgba(0,0,0,0.55)", backdropFilter: "blur(4px)" }}
            onClick={() => setMobileOpen(false)}
          />
        )}

        <div className="flex h-screen overflow-hidden">

          {/* ───────────── Sidebar ───────────── */}
          <aside
            className={`
              fixed md:relative z-50 h-full flex flex-col
              transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
              ${collapsed ? "md:w-[62px]" : "md:w-[230px]"}
              ${mobileOpen ? "translate-x-0 w-[230px]" : "-translate-x-full md:translate-x-0"}
            `}
            style={{
              background: "var(--bg-surface)",
              borderRight: "1px solid var(--border-subtle)",
              boxShadow: "4px 0 32px rgba(0,0,0,0.35)",
              transition: "width 0.3s cubic-bezier(0.16,1,0.3,1), transform 0.3s ease, background 0.38s, border-color 0.38s",
            }}
          >

            {/* Brand */}
            <div
              className="flex items-center gap-2.5 px-4 py-4 flex-shrink-0"
              style={{ borderBottom: "1px solid var(--border-subtle)" }}
            >
              <LogoMark />
              {!collapsed && (
                <div className="overflow-hidden min-w-0">
                  <p
                    className="text-[25px] font-bold leading-tight truncate"
                    style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}
                  >
                    LLM Control
                  </p>
                  <p
                    className="text-[15px] font-semibold tracking-widest uppercase truncate"
                    style={{ color: "var(--accent)" }}
                  >
                    Reliability
                  </p>
                </div>
              )}
            </div>

            {/* Nav */}
            <nav className="flex-1 p-2.5 space-y-0.5 overflow-y-auto overflow-x-hidden">
              {NAV_ITEMS.map(({ href, label, Icon }) => {
                const isActive = pathname === href || pathname.startsWith(href + "/");
                return (
                  <Link
                    key={href}
                    href={href}
                    title={collapsed ? label : undefined}
                    className={`nav-link ${isActive ? "active" : ""} ${collapsed ? "justify-center px-2" : ""}`}
                  >
                    <span className="flex-shrink-0" style={{ color: isActive ? "var(--accent)" : "var(--text-secondary)" }}>
                      <Icon size={16} />
                    </span>
                    {!collapsed && (
                      <span className="truncate">{label}</span>
                    )}
                    {isActive && !collapsed && (
                      <span
                        className="ml-auto w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ background: "var(--accent)", boxShadow: "0 0 6px var(--accent)" }}
                      />
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Bottom: theme toggle + collapse button */}
            <div
              className="p-2.5 flex-shrink-0 space-y-1"
              style={{ borderTop: "1px solid var(--border-subtle)" }}
            >
              {/* Theme toggle row */}
              <div
                className={`flex items-center rounded-xl px-2 py-2 ${collapsed ? "justify-center" : "gap-2.5"}` }
                style={{ background: "var(--bg-hover)" }}
              >
                {!collapsed && (
                  <>
                    <span style={{ color: "var(--text-secondary)" }}>
                      {isDark ? <IconMoon /> : <IconSun />}
                    </span>
                    <span
                      className="text-xs font-medium flex-1 truncate"
                      style={{ color: "var(--text-secondary)", fontFamily: "'Syne', sans-serif" }}
                    >
                      {isDark ? "Dark" : "Light"}
                    </span>
                  </>
                )}

                {/* Toggle pill */}
                <button
                  className="toggle-track"
                  onClick={() => setIsDark(!isDark)}
                  title={isDark ? "Switch to light" : "Switch to dark"}
                  style={{ background: isDark ? "#1a2744" : "var(--accent)" }}
                >
                  <div className="toggle-thumb" style={{ color: isDark ? "#ffd43b" : "#fff" }}>
                    {isDark ? "🌙" : "☀"}
                  </div>
                </button>
              </div>

              {/* Collapse button */}
              <button
                onClick={() => setCollapsed(!collapsed)}
                className={`w-full flex items-center rounded-xl px-2 py-2 transition-all ${collapsed ? "justify-center" : "gap-2.5"}`}
                style={{
                  color: "var(--text-secondary)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontFamily: "'Syne', sans-serif",
                  fontWeight: 500,
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-hover)")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <span className="flex-shrink-0">
                  {collapsed ? <IconChevronRight size={14} /> : <IconChevronLeft size={14} />}
                </span>
                {!collapsed && <span className="truncate text-xs" style={{ color: "var(--text-muted)" }}>Collapse</span>}
              </button>
            </div>
          </aside>

          {/* ───────────── Main ───────────── */}
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden" style={{ background: "var(--bg-base)", transition: "background 0.38s" }}>

            {/* Mobile topbar */}
            <div
              className="md:hidden flex items-center justify-between px-4 py-3 flex-shrink-0"
              style={{
                background: "var(--bg-surface)",
                borderBottom: "1px solid var(--border-subtle)",
                transition: "background 0.38s, border-color 0.38s",
              }}
            >
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setMobileOpen(true)}
                  className="w-9 h-9 rounded-xl flex items-center justify-center transition-all"
                  style={{
                    color: "var(--text-secondary)",
                    background: "var(--bg-hover)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <IconMenu />
                </button>
                <div className="flex items-center gap-2">
                  <LogoMark />
                  <span
                    className="text-sm font-bold"
                    style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}
                  >
                    LLM Control
                  </span>
                </div>
              </div>

              {/* Mobile theme toggle */}
              <button
                className="toggle-track"
                onClick={() => setIsDark(!isDark)}
                style={{ background: isDark ? "#1a2744" : "var(--accent)" }}
              >
                <div className="toggle-thumb" style={{ color: isDark ? "#ffd43b" : "#fff" }}>
                  {isDark ? "🌙" : "☀"}
                </div>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto grid-bg">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
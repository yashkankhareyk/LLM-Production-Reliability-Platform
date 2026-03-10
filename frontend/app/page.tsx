export default function HomePage() {
  return (
    <div className="min-h-full flex flex-col items-center px-6 pt-20 pb-24 relative overflow-hidden">

      {/* Ambient blobs */}
      <div
        className="absolute top-1/3 left-1/3 w-[500px] h-[500px] rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2"
        style={{ background: "radial-gradient(circle, rgba(79,124,255,0.06) 0%, transparent 68%)", filter: "blur(48px)" }}
      />
      <div
        className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(124,95,255,0.05) 0%, transparent 70%)", filter: "blur(40px)" }}
      />

      {/* ── Main card ── */}
      <div className="relative z-10 max-w-2xl w-full text-center animate-fadeIn">

        {/* Status badge */}
        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold tracking-widest uppercase"
          style={{
            background: "rgba(79,124,255,0.09)",
            border: "1px solid rgba(79,124,255,0.2)",
            color: "var(--accent)",
            fontFamily: "'Syne', sans-serif",
            marginBottom: "2rem",         /* 32px below badge */
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--accent-green)" }} />
          System Online
        </div>

        {/* Heading */}
        <h1
          className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.08]"
          style={{
            fontFamily: "'Syne', sans-serif",
            marginBottom: "1.5rem",       /* 24px below heading */
            marginTop: "4rem",              /* remove default margin above heading */
          }}
        >
          <span className="gradient-text">LLM Production</span>
          <br />
          <span style={{ color: "var(--text-primary)" }}>Reliability Platform</span>
        </h1>

        {/* Subtitle */}
        <p
          className="text-base sm:text-lg leading-relaxed max-w-md mx-auto"
          style={{
            color: "var(--text-secondary)",
            marginBottom: "3rem",   
            marginTop: "5rem",
            marginLeft: "auto",
            marginRight: "auto"                 /* 96px below subtitle before cards */      
          }}
        >
          Monitor, manage, and evaluate your language model pipelines with precision.
        </p>

        {/* Feature cards */}
        <div
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left"
          style={{ marginBottom: "2.5rem" }}  /* 40px below cards before CTA */
        >
          {[
            {
              href: "/chat",
              label: "Chat",
              desc: "Interact with your LLM in real-time",
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              ),
            },
            {
              href: "/ingest",
              label: "Ingest",
              desc: "Upload and process documents",
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              ),
            },
            {
              href: "/documents",
              label: "Documents",
              desc: "Browse your knowledge base",
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              ),
            },
          ].map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="card p-5 group cursor-pointer block"
              style={{ textDecoration: "none" }}
            >
              {/* Card icon + label */}
              <div className="flex items-center gap-3" style={{ marginBottom: "0.625rem" }}>
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{
                    background: "rgba(79,124,255,0.1)",
                    border: "1px solid rgba(79,124,255,0.18)",
                    color: "var(--accent)",
                  }}
                >
                  {item.icon}
                </div>
                <span
                  className="font-semibold text-sm"
                  style={{ fontFamily: "'Syne', sans-serif", color: "var(--text-primary)" }}
                >
                  {item.label}
                </span>
              </div>

              {/* Card desc */}
              <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {item.desc}
              </p>
            </a>
          ))}
        </div>


      </div>

      {/* Status bar — pinned to bottom */}
      <div
        className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-5 px-5 py-2 rounded-full text-[11px] font-medium tracking-wide whitespace-nowrap"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-subtle)",
          backdropFilter: "blur(12px)",
          fontFamily: "'Syne', sans-serif",
          boxShadow: "var(--shadow-card)",
          transition: "background 0.38s, border-color 0.38s",
        }}
      >
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--accent-green)" }} />
          <span style={{ color: "var(--text-secondary)" }}>API Connected</span>
        </span>
        <span className="w-px h-3" style={{ background: "var(--border-subtle)" }} />
        <span style={{ color: "var(--text-secondary)" }}>Use sidebar to navigate</span>
      </div>

    </div>
  );
}
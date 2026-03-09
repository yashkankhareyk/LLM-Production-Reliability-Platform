"use client";

import "./globals.css";
import Link from "next/link";
import { useState } from "react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  const [collapsed, setCollapsed] = useState(false);

  return (
    <html lang="en">
      <body className="bg-[#343541] text-white">

        <div className="flex h-screen">

          {/* Sidebar */}
          <aside
            className={`bg-[#202123] flex flex-col transition-all duration-300 ${
              collapsed ? "w-16" : "w-64"
            }`}
          >

            {/* Top */}
            <div className="p-6 border-b border-gray-700 flex items-center justify-between">

              {!collapsed && (
                <h1 className="text-lg font-semibold text-gray-400">
                   LLM Control
                </h1>
              )}

              {/* Toggle Button */}
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="text-gray-400 hover:text-white transition"
              >
                ☰
              </button>

            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-2 text-sm">

              <Link
                href="/chat"
                className="block px-3 py-2 rounded-md text-gray-400 hover:bg-gray-700 transition"
              >
                💬 {!collapsed && "Chat"}
              </Link>

              <Link
                href="/ingest"
                className="block px-3 py-2 rounded-md text-gray-400 hover:bg-gray-700 transition"
              >
                📂 {!collapsed && "Ingest Files"}
              </Link>
  
              <Link
                href="/documents"
                className="block px-3 py-2 rounded-md text-gray-400 hover:bg-gray-700 transition"
              >
                📄 {!collapsed && "Documents"}
              </Link>

            </nav>

            {/* Bottom */}
            {!collapsed && (
              <div className="mt-auto p-4 text-xs text-gray-400 border-t border-gray-700">
                AI Reliability Platform
              </div>
            )}

          </aside>

          {/* Main */}
          <main className="flex-1 flex flex-col bg-[#343541]">
            <div className="flex-1 overflow-y-auto">
              {children}
            </div>
          </main>

        </div>

      </body>
    </html>
  );
}
import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "LLM Control Plane",
  description: "LLM Production Reliability Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white">
        <div className="flex h-screen">

          {/* Sidebar */}
          <aside className="w-64 bg-gray-900 border-r border-gray-800 p-6">
            <h1 className="text-xl font-bold mb-8">
              LLM Control Plane
            </h1>

            <nav className="space-y-4 text-gray-300">
              <Link href="/chat" className="block hover:text-white">
                Chat
              </Link>
              <Link href="/runs" className="block hover:text-white">
                Runs
              </Link>
              <Link href="/dashboard" className="block hover:text-white">
                Dashboard
              </Link>
              <Link href="/alerts" className="block hover:text-white">
                Alerts
              </Link>
              <Link href="/eval" className="block hover:text-white">
                Evaluation
              </Link>
            </nav>
          </aside>

          {/* Main */}
          <main className="flex-1 p-8 overflow-y-auto">
            {children}
          </main>

        </div>
      </body>
    </html>
  );
}
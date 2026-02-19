"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/auth";

const DOCS_READER_PATTERN = /^\/inmate\/documents\/[^/]+$/;

const tabs = [
  { href: "/inmate", label: "My Case", icon: "📋" },
  { href: "/inmate/documents", label: "Documents", icon: "📄" },
  { href: "/inmate/similar", label: "Similar Cases", icon: "🔍" },
  { href: "/inmate/help", label: "Help", icon: "❓" },
] as const;

export default function InmateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user } = useAuth();

  if (user && user.role !== "inmate") {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <p className="text-lg text-gray-600">Inmate only. Redirecting…</p>
      </div>
    );
  }

  const isReader = pathname ? DOCS_READER_PATTERN.test(pathname) : false;

  return (
    <div
      className={`flex min-h-screen flex-col bg-stone-50 ${isReader ? "" : "pb-20 md:pb-24"}`}
    >
      {!isReader && (
        <header className="sticky top-0 z-40 border-b border-stone-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
          <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
            <h1 className="text-lg font-semibold text-stone-800">My Case</h1>
            <Link
              href="/"
              className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-full text-stone-500 hover:bg-stone-100"
              aria-label="Home"
            >
              🏠
            </Link>
          </div>
        </header>
      )}
      <main className="flex-1">{children}</main>

      {/* Bottom navigation - min 48px touch targets (hidden in reader) */}
      {!isReader && (
      <nav
        className="fixed bottom-0 left-0 right-0 z-50 border-t border-stone-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80"
        aria-label="Inmate navigation"
      >
        <div className="mx-auto flex max-w-2xl">
          {tabs.map(({ href, label, icon }) => {
            const isActive =
              href === "/inmate"
                ? pathname === "/inmate"
                : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className="min-h-[56px] flex-1 flex flex-col items-center justify-center gap-0.5 px-2 py-3 text-center transition-colors active:bg-stone-100"
                style={{ minHeight: 48 }}
              >
                <span className="text-xl" aria-hidden>
                  {icon}
                </span>
                <span
                  className={`text-xs font-medium md:text-sm ${
                    isActive ? "text-amber-700" : "text-stone-500"
                  }`}
                >
                  {label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
      )}
    </div>
  );
}

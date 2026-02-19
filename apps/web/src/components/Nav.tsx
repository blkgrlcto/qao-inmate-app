"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth";

export function Nav() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const isStaff = user.role === "attorney" || user.role === "paralegal";

  return (
    <nav className="border-b border-gray-200 bg-white px-4 py-2">
      <div className="flex items-center justify-between">
        <div className="flex gap-4">
          <Link href="/" className="font-medium text-gray-900 hover:text-blue-600">
            Home
          </Link>
          {isStaff ? (
            <>
              <Link
                href="/cases"
                className="font-medium text-gray-600 hover:text-blue-600"
              >
                Cases
              </Link>
              <Link
                href="/cases/federal"
                className="font-medium text-gray-600 hover:text-blue-600"
              >
                Federal Search
              </Link>
            </>
          ) : (
            <Link
              href="/inmate"
              className="font-medium text-gray-600 hover:text-blue-600"
            >
              My Documents
            </Link>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            {user.full_name} ({user.role})
          </span>
          <button
            onClick={logout}
            className="text-sm text-gray-600 hover:text-red-600"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

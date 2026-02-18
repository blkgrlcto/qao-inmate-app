"use client";

import Link from "next/link";
import { useAuth } from "@/context/auth";

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-gray-600">Sign in to continue</p>
        <Link
          href="/login"
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
        >
          Sign in
        </Link>
      </div>
    );
  }

  const isStaff = user.role === "attorney" || user.role === "paralegal";
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-xl font-semibold">Welcome, {user.full_name}</h1>
      <div className="flex gap-4">
        {isStaff ? (
          <Link
            href="/cases"
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            View Cases
          </Link>
        ) : (
          <Link
            href="/inmate"
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            My Documents
          </Link>
        )}
      </div>
    </div>
  );
}

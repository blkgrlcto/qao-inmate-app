"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/context/auth";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user && user.role !== "admin") router.replace("/");
  }, [loading, user, router]);

  if (loading) return <div className="p-6">Loading…</div>;
  if (!user || user.role !== "admin") {
    return (
      <div className="p-6">
        <p className="text-gray-600">Admin only. Redirecting…</p>
      </div>
    );
  }

  return <>{children}</>;
}

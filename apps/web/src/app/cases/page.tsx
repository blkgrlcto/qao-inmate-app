"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import * as api from "@/lib/api";

type CaseRow = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  updated_at: string;
};

export default function CasesPage() {
  const { token, user } = useAuth();
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || (user && user.role === "inmate")) return;
    api
      .listCases(token)
      .then(setCases)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [token, user]);

  if (user?.role === "inmate") {
    return (
      <div className="p-6">
        <p className="text-gray-600">Staff only. Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="mb-4 text-xl font-semibold">Cases</h1>
      {error && <p className="mb-2 text-red-600">{error}</p>}
      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : cases.length === 0 ? (
        <p className="text-gray-500">No cases yet.</p>
      ) : (
        <ul className="space-y-2">
          {cases.map((c) => (
            <li key={c.id}>
              <Link
                href={`/cases/${c.id}`}
                className="block rounded border border-gray-200 p-3 hover:bg-gray-50"
              >
                <span className="font-medium">{c.title}</span>
                {c.description && (
                  <span className="ml-2 text-sm text-gray-500">
                    {c.description}
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

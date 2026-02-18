"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import * as api from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  case_title: string;
  case_id: string;
};

export default function InmatePage() {
  const { token, user } = useAuth();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || (user && user.role !== "inmate")) return;
    api
      .listInmateDocs(token)
      .then(setDocs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [token, user]);

  if (user && user.role !== "inmate") {
    return (
      <div className="p-6">
        <p className="text-gray-600">Inmate only. Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="mb-4 text-xl font-semibold">My Documents</h1>
      {error && <p className="mb-2 text-red-600">{error}</p>}
      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : docs.length === 0 ? (
        <p className="text-gray-500">No documents shared with you yet.</p>
      ) : (
        <ul className="space-y-2">
          {docs.map((d) => (
            <li key={d.id}>
              <Link
                href={`/files/${d.id}`}
                className="block rounded border border-gray-200 p-3 hover:bg-gray-50"
              >
                <span className="font-medium">{d.title}</span>
                <span className="ml-2 text-sm text-gray-500">
                  ({d.case_title})
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

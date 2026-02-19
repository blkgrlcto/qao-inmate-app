"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import { EmptyState } from "@/components/inmate/EmptyState";
import { ErrorState } from "@/components/inmate/ErrorState";
import { SkeletonList } from "@/components/inmate/SkeletonCard";
import * as api from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  case_title: string;
  case_id: string;
};

type Filter = "all" | "new" | "offline" | "important";

export default function InmateDocumentsPage() {
  const { token, user } = useAuth();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");

  const load = useCallback(() => {
    if (!token || (user && user.role !== "inmate")) return;
    setLoading(true);
    setError("");
    api
      .listInmateDocs(token)
      .then(setDocs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [token, user]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = docs.filter((d) => {
    const matchesSearch =
      !search ||
      d.title.toLowerCase().includes(search.toLowerCase()) ||
      d.case_title.toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;
    if (filter === "all") return true;
    if (filter === "new") return docs.indexOf(d) < 3;
    if (filter === "offline") return false;
    if (filter === "important") return false;
    return true;
  });

  const filters: { key: Filter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "new", label: "New" },
    { key: "offline", label: "Offline" },
    { key: "important", label: "Important" },
  ];

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 text-base">
      {error && (
        <div className="mb-4">
          <ErrorState message={error} onRetry={load} />
        </div>
      )}

      {/* Search bar */}
      <div className="mb-4">
        <input
          type="search"
          placeholder="Search documents…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-h-[48px] w-full rounded-xl border border-stone-200 bg-white px-4 py-3 text-base shadow-sm focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/20"
        />
      </div>

      {/* Filter chips */}
      <div className="mb-6 flex flex-wrap gap-2">
        {filters.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`min-h-[44px] rounded-full px-5 py-2 text-base font-medium transition ${
              filter === key
                ? "bg-amber-500 text-white shadow"
                : "bg-stone-100 text-stone-600 hover:bg-stone-200"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <SkeletonList count={5} />
      ) : docs.length === 0 ? (
        <EmptyState
          icon="📄"
          title="No documents yet"
          message="Documents shared by your attorney will appear here."
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="🔍"
          title="No matches"
          message="Try a different search or filter."
        />
      ) : (
        <ul className="space-y-4">
          {filtered.map((d) => (
            <li key={d.id}>
              <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <Link
                    href={`/inmate/documents/${d.id}`}
                    className="min-h-[48px] flex-1 py-1"
                  >
                    <h3 className="font-semibold text-stone-800">{d.title}</h3>
                    <p className="mt-0.5 text-sm text-stone-500">
                      {d.case_title}
                    </p>
                  </Link>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-medium text-stone-500">
                      PDF
                    </span>
                    <a
                      href={`/apiProxy/files/${d.id}/stream`}
                      download={d.title.replace(/\.pdf$/i, "") + ".pdf"}
                      className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-full bg-stone-100 text-stone-600 hover:bg-stone-200 active:scale-95"
                      aria-label={`Download ${d.title}`}
                    >
                      ⬇️
                    </a>
                  </div>
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

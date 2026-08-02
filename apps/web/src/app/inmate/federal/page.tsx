"use client";

import { useCallback, useState } from "react";
import { useAuth } from "@/context/auth";
import type { FederalCaseResult } from "@/lib/api";
import { EmptyState } from "@/components/inmate/EmptyState";
import { ErrorState } from "@/components/inmate/ErrorState";
import { SkeletonList } from "@/components/inmate/SkeletonCard";
import * as api from "@/lib/api";

export default function InmateFederalSearchPage() {
  const { user } = useAuth();
  const [q, setQ] = useState("");
  const [courtId, setCourtId] = useState("");
  const [results, setResults] = useState<FederalCaseResult[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [detectedMode, setDetectedMode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const search = useCallback(() => {
    if (!user || !q.trim()) return;
    setLoading(true);
    setError("");
    setSearched(true);
    api
      .searchFederalCases({
        q: q.trim(),
        court_id: courtId.trim() || undefined,
        limit: 20,
      })
      .then((data: {
        results?: FederalCaseResult[];
        next_cursor?: string | null;
        detected_mode?: string;
      }) => {
        setResults(data.results || []);
        setNextCursor(data.next_cursor || null);
        setDetectedMode(data.detected_mode || null);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Search failed");
        setResults([]);
      })
      .finally(() => setLoading(false));
  }, [user, q, courtId]);

  const loadMore = useCallback(() => {
    if (!user || !q.trim() || !nextCursor) return;
    setLoading(true);
    api
      .searchFederalCases({
        q: q.trim(),
        court_id: courtId.trim() || undefined,
        limit: 20,
        cursor: nextCursor,
      })
      .then((data: {
        results?: FederalCaseResult[];
        next_cursor?: string | null;
      }) => {
        setResults((prev) => [...prev, ...(data.results || [])]);
        setNextCursor(data.next_cursor || null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load more failed"))
      .finally(() => setLoading(false));
  }, [user, q, courtId, nextCursor]);

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 text-base">
      <h2 className="mb-4 text-lg font-semibold text-stone-800">
        Federal Case Search
      </h2>
      <p className="mb-4 text-stone-600">
        Search federal court dockets. Enter a docket number (e.g. 1:23-cv-01234) or a party name.
      </p>

      {error && (
        <div className="mb-4">
          <ErrorState message={error} onRetry={search} />
        </div>
      )}

      <div className="mb-4 flex gap-2">
        <input
          type="search"
          placeholder="Docket number or party name…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          className="min-h-[48px] flex-1 rounded-xl border border-stone-200 bg-white px-4 py-3 text-base shadow-sm focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/20"
        />
        <button
          onClick={search}
          disabled={loading || !q.trim()}
          className="min-h-[48px] min-w-[48px] flex shrink-0 items-center justify-center rounded-xl bg-amber-500 text-white disabled:opacity-50"
        >
          {loading ? "…" : "🔍"}
        </button>
      </div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Court ID (optional)"
          value={courtId}
          onChange={(e) => setCourtId(e.target.value)}
          className="min-h-[44px] w-full rounded-xl border border-stone-200 bg-white px-4 py-2 text-base"
        />
      </div>

      {detectedMode && (
        <p className="mb-4 text-sm text-stone-500">
          Search type: <strong>{detectedMode}</strong>
        </p>
      )}

      {loading && results.length === 0 ? (
        <SkeletonList count={5} />
      ) : searched && results.length === 0 ? (
        <EmptyState
          icon="🔍"
          title="No results"
          message="Try a different docket number or party name."
        />
      ) : results.length > 0 ? (
        <>
          <ul className="space-y-4">
            {results.map((r) => (
              <li key={r.id}>
                <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-semibold text-stone-800">
                        {r.case_name || "Untitled"}
                      </h3>
                      {r.docket_number && (
                        <p className="mt-1 text-sm text-stone-500">
                          {r.docket_number}
                          {r.court_id && ` · ${r.court_id}`}
                        </p>
                      )}
                      {r.date_filed && (
                        <p className="text-sm text-stone-500">
                          Filed: {r.date_filed}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {r.recap_available && (
                        <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800">
                          RECAP
                        </span>
                      )}
                      {r.absolute_url && (
                        <a
                          href={r.absolute_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="min-h-[44px] rounded-xl bg-amber-100 px-4 py-2 text-sm font-medium text-amber-800 hover:bg-amber-200"
                        >
                          View source →
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              </li>
            ))}
          </ul>
          {nextCursor && (
            <button
              onClick={loadMore}
              disabled={loading}
              className="mt-6 min-h-[48px] w-full rounded-xl border-2 border-stone-200 bg-white font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-50"
            >
              {loading ? "Loading…" : "Load more"}
            </button>
          )}
        </>
      ) : (
        <EmptyState
          icon="⚖️"
          title="Search federal cases"
          message="Enter a docket number (e.g. 1:23-cv-01234) or a party name above to search PACER/RECAP."
        />
      )}
    </div>
  );
}

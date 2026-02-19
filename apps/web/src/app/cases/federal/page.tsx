"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { useAuth } from "@/context/auth";
import type { FederalCaseResult } from "@/lib/api";
import { EmptyState } from "@/components/inmate/EmptyState";
import { ErrorState } from "@/components/inmate/ErrorState";
import { SkeletonList } from "@/components/inmate/SkeletonCard";
import * as api from "@/lib/api";

export default function FederalCaseSearchPage() {
  const { token } = useAuth();
  const [q, setQ] = useState("");
  const [courtId, setCourtId] = useState("");
  const [results, setResults] = useState<FederalCaseResult[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [detectedMode, setDetectedMode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const search = useCallback(() => {
    if (!token || !q.trim()) return;
    setLoading(true);
    setError("");
    setSearched(true);
    api
      .searchFederalCases(token, {
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
  }, [token, q, courtId]);

  const loadMore = useCallback(() => {
    if (!token || !q.trim() || !nextCursor) return;
    setLoading(true);
    api
      .searchFederalCases(token, {
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
  }, [token, q, courtId, nextCursor]);

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <Link href="/cases" className="mb-4 inline-block text-blue-600 hover:underline">
        ← Back to cases
      </Link>
      <h1 className="mb-6 text-xl font-semibold">Federal Case Search</h1>
      <p className="mb-4 text-stone-600">
        Search PACER/RECAP federal dockets. Enter a docket number (e.g. 1:23-cv-01234) or a party name.
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
          className="min-h-[48px] rounded-xl bg-amber-500 px-6 py-2 font-medium text-white disabled:opacity-50"
        >
          Search
        </button>
      </div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Court ID (optional, e.g. nysd, cacd)"
          value={courtId}
          onChange={(e) => setCourtId(e.target.value)}
          className="min-h-[40px] w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm"
        />
      </div>

      {detectedMode && (
        <p className="mb-4 text-sm text-stone-500">
          Detected: <strong>{detectedMode}</strong> search
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
                  <div className="flex items-start justify-between gap-4">
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
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
                          RECAP
                        </span>
                      )}
                      {r.absolute_url && (
                        <a
                          href={r.absolute_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="min-h-[44px] rounded-xl bg-stone-100 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-200"
                        >
                          View →
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
          message="Enter a docket number (e.g. 1:23-cv-01234) or a party name above."
        />
      )}
    </div>
  );
}

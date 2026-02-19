"use client";

import { useCallback, useState } from "react";
import { useAuth } from "@/context/auth";
import type { SimilarResult } from "@/lib/api";
import { EmptyState } from "@/components/inmate/EmptyState";
import { ErrorState } from "@/components/inmate/ErrorState";
import { SkeletonList } from "@/components/inmate/SkeletonCard";
import * as api from "@/lib/api";

const SUGGESTED_QUERIES = [
  "habeas corpus appeal",
  "ineffective assistance of counsel",
  "sentencing modification",
  "parole eligibility",
];

const JURISDICTIONS = ["All", "US", "PA", "Federal", "State"];
const DISPOSITIONS = ["All", "AFFIRMED", "REVERSED", "VACATED", "REMANDED", "DISMISSED"];

export default function InmateSimilarPage() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [jurisdiction, setJurisdiction] = useState("All");
  const [dispositions, setDispositions] = useState<string[]>(["All"]);
  const [results, setResults] = useState<SimilarResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const search = useCallback(() => {
    if (!token || !query.trim()) return;
    setLoading(true);
    setError("");
    setHasSearched(true);
    const dispositionParams =
      dispositions.includes("All") || dispositions.length === 0
        ? undefined
        : dispositions;
    api
      .searchSimilar(token, {
        q: query.trim(),
        jurisdiction: jurisdiction === "All" ? undefined : jurisdiction,
        disposition: dispositionParams,
        limit: 10,
      })
      .then((data: { results?: SimilarResult[] }) => setResults(data.results || []))
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Search failed");
        setResults([]);
      })
      .finally(() => setLoading(false));
  }, [token, query, jurisdiction, dispositions]);

  const toggleDisposition = (d: string) => {
    if (d === "All") {
      setDispositions(["All"]);
      return;
    }
    setDispositions((prev) => {
      const next = prev.filter((x) => x !== "All" && x !== d);
      if (prev.includes(d)) return next.length ? next : ["All"];
      return [...next, d];
    });
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 text-base">
      {error && (
        <div className="mb-4">
          <ErrorState message={error} onRetry={search} />
        </div>
      )}

      {/* Search prompt */}
      <div className="mb-6">
        <label htmlFor="similar-search" className="mb-2 block text-base font-medium text-stone-700">
          Find similar cases
        </label>
        <div className="flex gap-2">
          <input
            id="similar-search"
            aria-label="Search for similar cases"
            type="search"
            placeholder="e.g. habeas corpus appeal"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
            className="min-h-[48px] flex-1 rounded-xl border border-stone-200 bg-white px-4 py-3 text-base shadow-sm focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/20"
          />
          <button
            onClick={search}
            disabled={loading || !query.trim()}
            className="min-h-[48px] min-w-[48px] flex shrink-0 items-center justify-center rounded-xl bg-amber-500 text-white shadow disabled:opacity-50"
          >
            {loading ? "…" : "🔍"}
          </button>
        </div>
      </div>

      {/* Suggested queries */}
      <div className="mb-6">
        <p className="mb-2 text-sm text-stone-500">Try searching for:</p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUERIES.map((suggested) => (
            <button
              key={suggested}
              onClick={() => {
                setQuery(suggested);
                if (token) {
                  setLoading(true);
                  setError("");
                  setHasSearched(true);
                  api
                    .searchSimilar(token, { q: suggested, limit: 10 })
                    .then((d: { results?: SimilarResult[] }) => setResults(d.results || []))
                    .catch((e) => {
                      setError(e instanceof Error ? e.message : "Search failed");
                      setResults([]);
                    })
                    .finally(() => setLoading(false));
                }
              }}
              className="min-h-[44px] rounded-full bg-stone-100 px-4 py-2 text-base text-stone-700 hover:bg-stone-200"
            >
              {suggested}
            </button>
          ))}
        </div>
      </div>

      {/* Jurisdiction + disposition filters */}
      <div className="mb-6 space-y-3">
        <p className="text-sm font-medium text-stone-600">Filters</p>
        <div className="flex flex-wrap gap-2">
          {JURISDICTIONS.map((j) => (
            <button
              key={j}
              onClick={() => setJurisdiction(j)}
              className={`min-h-[44px] rounded-full px-4 py-2 text-base font-medium ${
                jurisdiction === j ? "bg-amber-500 text-white" : "bg-stone-100 text-stone-600"
              }`}
            >
              {j}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {DISPOSITIONS.map((d) => (
            <button
              key={d}
              onClick={() => toggleDisposition(d)}
              className={`min-h-[44px] rounded-full px-4 py-2 text-base font-medium ${
                dispositions.includes(d) ? "bg-amber-500 text-white" : "bg-stone-100 text-stone-600"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <SkeletonList count={5} />
      ) : hasSearched && results.length === 0 ? (
        <EmptyState
          icon="🔍"
          title="No similar cases found"
          message="Try different keywords or broaden your filters. The Similar Cases feature finds court opinions that match your situation."
        />
      ) : results.length > 0 ? (
        <ul className="space-y-4">
          {results.map((r) => (
            <SimilarResultCard key={r.id} result={r} />
          ))}
        </ul>
      ) : (
        <EmptyState
          icon="📚"
          title="Search for similar cases"
          message="Enter a legal topic or issue above to find court opinions that may be relevant to your situation."
        />
      )}
    </div>
  );
}

function SimilarResultCard({ result }: { result: SimilarResult }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li>
      <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
        <div className="flex items-start gap-2">
          <span
            className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
              result.disposition === "AFFIRMED"
                ? "bg-emerald-100 text-emerald-800"
                : result.disposition === "REVERSED"
                  ? "bg-amber-100 text-amber-800"
                  : "bg-stone-100 text-stone-600"
            }`}
          >
            {result.disposition}
          </span>
          <span className="text-xs text-stone-500">{result.jurisdiction}</span>
        </div>
        <h3 className="mt-2 font-semibold text-stone-800">{result.title}</h3>
        {result.citation && (
          <p className="mt-0.5 text-sm text-stone-500">{result.citation}</p>
        )}
        {result.headline && (
          <p className="mt-2 text-stone-600">{result.headline}</p>
        )}
        {result.pull_quotes && result.pull_quotes.length > 0 && (
          <blockquote className="mt-2 border-l-4 border-amber-400 pl-3 text-stone-600 italic">
            &ldquo;{result.pull_quotes[0]}&rdquo;
          </blockquote>
        )}

        {/* Why this matched accordion */}
        {result.why && (result.why.keyword_matches?.length || result.why.similarity_bucket) && (
          <div className="mt-4">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex min-h-[48px] w-full items-center justify-between rounded-xl bg-stone-50 px-4 py-3 text-left font-medium text-stone-700"
            >
              Why this result?
              <span className="text-xl">{expanded ? "−" : "+"}</span>
            </button>
            {expanded && (
              <div className="mt-2 rounded-xl border border-stone-200 bg-stone-50/50 p-4 text-sm text-stone-600">
                {result.why.similarity_bucket && (
                  <p>
                    <strong>Relevance:</strong> {result.why.similarity_bucket}
                  </p>
                )}
                {result.why.keyword_matches && result.why.keyword_matches.length > 0 && (
                  <p className="mt-2">
                    <strong>Keyword matches:</strong>{" "}
                    {result.why.keyword_matches.join(", ")}
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {result.source_url && (
          <a
            href={result.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block min-h-[44px] rounded-xl bg-stone-100 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-200"
          >
            View source →
          </a>
        )}
      </article>
    </li>
  );
}

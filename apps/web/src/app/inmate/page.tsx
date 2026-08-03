"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import { EmptyState } from "@/components/inmate/EmptyState";
import { ErrorState } from "@/components/inmate/ErrorState";
import { SkeletonList } from "@/components/inmate/SkeletonCard";
import { StatusBadge } from "@/components/StatusBadge";
import * as api from "@/lib/api";
import type { AskResponse, Deadline } from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  case_title: string;
  case_id: string;
};

export default function InmateMyCasePage() {
  const { user } = useAuth();
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [caseStatus, setCaseStatus] = useState<string | null>(null);
  const [nextDeadline, setNextDeadline] = useState<Deadline | null>(null);
  const [caseId, setCaseId] = useState<string | null>(null);

  const [question, setQuestion] = useState("");
  const [askResult, setAskResult] = useState<AskResponse | null>(null);
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");

  const load = useCallback(() => {
    if (!user || user.role !== "inmate") return;
    setLoading(true);
    setError("");
    api
      .listInmateDocs()
      .then((data) => {
        setDocs(data);
        setLastSync(new Date());
        const cid = data[0]?.case_id;
        setCaseId(cid || null);
        if (cid) {
          api.getCase(cid).then((c) => setCaseStatus(c.status)).catch(() => {});
          api
            .listDeadlines(cid)
            .then((ds: Deadline[]) => {
              const today = new Date().toISOString().slice(0, 10);
              setNextDeadline(ds.find((d) => d.due_date >= today) || null);
            })
            .catch(() => {});
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || !caseId) return;
    setAsking(true);
    setAskError("");
    setAskResult(null);
    try {
      const res = await api.askAboutCase(caseId, question.trim());
      setAskResult(res);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : "Failed to get an answer");
    } finally {
      setAsking(false);
    }
  }

  useEffect(() => {
    load();
  }, [load]);

  const isOnline = typeof navigator !== "undefined" ? navigator.onLine : true;
  const caseTitle = docs[0]?.case_title || "Your Case";
  const newItems = docs.slice(0, 3);
  const lastDoc = docs[0];

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 text-base">
      {error && (
        <div className="mb-4">
          <ErrorState message={error} onRetry={load} />
        </div>
      )}

      {loading ? (
        <div className="space-y-6">
          <div className="h-24 animate-pulse rounded-2xl bg-stone-200" />
          <SkeletonList count={3} />
        </div>
      ) : docs.length === 0 ? (
        <EmptyState
          icon="📋"
          title="No documents yet"
          message="Your attorney will share documents with you here. Check back soon."
        />
      ) : (
        <div className="space-y-6">
          {/* Case header */}
          <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-stone-800">{caseTitle}</h2>
              {caseStatus && <StatusBadge status={caseStatus} />}
            </div>
            <p className="mt-1 text-stone-600">
              {docs.length} document{docs.length !== 1 ? "s" : ""} shared with
              you
            </p>
            {nextDeadline && (
              <p className="mt-2 text-sm font-medium text-amber-700">
                Next deadline: {nextDeadline.title} ({nextDeadline.due_date})
              </p>
            )}
          </div>

          {/* Ask about your case */}
          <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
            <h3 className="mb-1 text-base font-semibold text-stone-800">
              Ask about your case
            </h3>
            <p className="mb-3 text-sm text-stone-500">
              Answers only use documents shared with you, with sources shown below.
            </p>
            <form onSubmit={handleAsk} className="mb-3 flex flex-col gap-2 sm:flex-row">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. What is my next court date?"
                className="min-h-[48px] flex-1 rounded-xl border border-stone-200 bg-white px-4 py-3 text-base shadow-sm focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/20"
              />
              <button
                type="submit"
                disabled={asking || !question.trim()}
                className="min-h-[48px] rounded-xl bg-amber-500 px-6 py-2 font-medium text-white disabled:opacity-50"
              >
                {asking ? "Asking…" : "Ask"}
              </button>
            </form>
            {askError && <p className="mb-2 text-sm text-red-600">{askError}</p>}
            {askResult && (
              <div className="rounded-xl bg-stone-50 p-4 text-sm text-stone-700">
                <p className="whitespace-pre-wrap">{askResult.answer}</p>
                {askResult.citations.length > 0 && (
                  <div className="mt-3 border-t border-stone-200 pt-2">
                    <p className="mb-1 text-xs font-medium text-stone-500">Sources</p>
                    <ul className="space-y-1">
                      {askResult.citations.map((c, i) => (
                        <li key={i} className="text-xs text-stone-600">
                          <span className="font-medium">{c.document_title}</span>
                          {" — "}
                          <span className="italic">&ldquo;{c.snippet}&rdquo;</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* New items card */}
          {newItems.length > 0 && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-5">
              <h3 className="mb-3 text-base font-semibold text-stone-800">
                New items
              </h3>
              <ul className="space-y-2">
                {newItems.map((d) => (
                  <li key={d.id}>
                    <Link
                      href={`/inmate/documents/${d.id}`}
                      className="block rounded-xl border border-amber-200 bg-white p-4 text-stone-800 transition hover:border-amber-300 hover:bg-amber-50/30 active:scale-[0.99]"
                    >
                      <span className="font-medium">{d.title}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Continue reading */}
          {lastDoc && (
            <Link
              href={`/inmate/documents/${lastDoc.id}`}
              className="flex min-h-[56px] w-full items-center justify-between rounded-2xl border-2 border-stone-200 bg-white px-6 py-4 text-left shadow-sm transition hover:border-amber-300 hover:bg-amber-50/30 active:scale-[0.99]"
            >
              <span className="text-base font-medium text-stone-800">
                Continue reading
              </span>
              <span className="text-2xl">→</span>
            </Link>
          )}

          {/* Offline status + last sync */}
          <div className="flex items-center justify-between rounded-xl border border-stone-200 bg-white px-4 py-3">
            <span className="flex items-center gap-2 text-sm text-stone-600">
              <span
                className={`inline-block h-2.5 w-2.5 rounded-full ${
                  isOnline ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {isOnline ? "Online" : "Offline"}
            </span>
            {lastSync && (
              <span className="text-sm text-stone-500">
                Last sync: {lastSync.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

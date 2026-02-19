"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import * as api from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  case_title: string;
  case_id: string;
};

export default function InmateDocumentReaderPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;
  const { token } = useAuth();
  const [doc, setDoc] = useState<Doc | null>(null);
  const [loading, setLoading] = useState(true);
  const [bookmarked, setBookmarked] = useState(false);
  const [savedOffline, setSavedOffline] = useState(false);

  useEffect(() => {
    const stored = typeof localStorage !== "undefined" && localStorage.getItem(`bookmark-${docId}`);
    setBookmarked(stored === "true");
  }, [docId]);

  const loadDoc = useCallback(() => {
    if (!token) return;
    api
      .listInmateDocs(token)
      .then((list: Doc[]) => {
        const found = list.find((d: Doc) => d.id === docId);
        setDoc(found || null);
      })
      .finally(() => setLoading(false));
  }, [token, docId]);

  useEffect(() => {
    loadDoc();
  }, [loadDoc]);

  const toggleBookmark = () => {
    const next = !bookmarked;
    setBookmarked(next);
    if (typeof localStorage !== "undefined") {
      if (next) localStorage.setItem(`bookmark-${docId}`, "true");
      else localStorage.removeItem(`bookmark-${docId}`);
    }
  };

  const proxyUrl = `/apiProxy/files/${docId}/stream`;

  return (
    <div className="flex min-h-screen flex-col">
      {/* Sticky top bar */}
      <header className="sticky top-0 z-50 flex min-h-[56px] items-center justify-between border-b border-stone-200 bg-white px-4 shadow-sm">
        <button
          onClick={() => router.back()}
          className="min-h-[44px] min-w-[44px] -ml-1 flex items-center justify-center rounded-full text-stone-600 hover:bg-stone-100"
          aria-label="Back"
        >
          ←
        </button>
        <h1 className="flex-1 truncate px-2 text-center text-base font-semibold text-stone-800">
          {loading ? "Loading…" : doc?.title || "Document"}
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSavedOffline(!savedOffline)}
            className={`min-h-[44px] rounded-xl px-4 py-2 text-sm font-medium ${
              savedOffline
                ? "bg-amber-500 text-white"
                : "bg-stone-100 text-stone-600 hover:bg-stone-200"
            }`}
          >
            {savedOffline ? "Saved" : "Save offline"}
          </button>
          <button
            onClick={toggleBookmark}
            className={`min-h-[44px] min-w-[44px] flex items-center justify-center rounded-full ${
              bookmarked ? "text-amber-500" : "text-stone-400 hover:text-stone-600"
            }`}
            aria-label={bookmarked ? "Remove bookmark" : "Add bookmark"}
          >
            {bookmarked ? "🔖" : "📑"}
          </button>
        </div>
      </header>

      {/* PDF viewer */}
      <div className="flex-1 overflow-hidden bg-stone-100">
        {loading && !doc ? (
          <div className="flex h-full items-center justify-center">
            <div className="animate-pulse text-stone-400">Loading…</div>
          </div>
        ) : !doc ? (
          <div className="flex h-full flex-col items-center justify-center p-8">
            <p className="text-stone-600">Document not found.</p>
            <Link
              href="/inmate/documents"
              className="mt-4 min-h-[48px] rounded-xl bg-amber-500 px-6 py-3 font-medium text-white"
            >
              Back to documents
            </Link>
          </div>
        ) : (
          <object
            data={proxyUrl}
            type="application/pdf"
            className="h-full w-full"
            aria-label="PDF document"
          >
            <div className="flex h-full flex-col items-center justify-center p-8 text-center">
              <p className="text-stone-600">PDF cannot be displayed.</p>
              <a
                href={proxyUrl}
                download
                className="mt-4 min-h-[48px] inline-flex items-center justify-center rounded-xl bg-amber-500 px-6 py-3 font-medium text-white"
              >
                Download instead
              </a>
            </div>
          </object>
        )}
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import * as api from "@/lib/api";

type Doc = {
  id: string;
  title: string;
  created_at: string;
  inmate_visible: boolean;
};

type CaseDetail = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  updated_at: string;
};

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;
  const { token } = useAuth();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const loadCase = useCallback(() => {
    if (!token) return;
    api.getCase(token, caseId).then(setCaseData).catch(setError);
  }, [token, caseId]);

  const loadDocs = useCallback(() => {
    if (!token) return;
    api
      .listCaseDocs(token, caseId, search || undefined)
      .then(setDocs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"))
      .finally(() => setLoading(false));
  }, [token, caseId, search]);

  useEffect(() => {
    if (!token || !caseId) return;
    setLoading(true);
    loadCase();
    loadDocs();
  }, [token, caseId, loadCase, loadDocs]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadDoc(token, caseId, file, false);
      loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function toggleInmateVisible(docId: string, current: boolean) {
    if (!token) return;
    try {
      await api.updateDocInmateVisible(token, docId, !current);
      setDocs((prev) =>
        prev.map((d) =>
          d.id === docId ? { ...d, inmate_visible: !current } : d
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  if (!caseData) return <div className="p-6">Loading…</div>;

  return (
    <div className="p-6">
      <Link href="/cases" className="mb-4 inline-block text-blue-600 hover:underline">
        ← Back to cases
      </Link>
      <h1 className="mb-2 text-xl font-semibold">{caseData.title}</h1>
      {caseData.description && (
        <p className="mb-4 text-gray-600">{caseData.description}</p>
      )}
      {error && <p className="mb-2 text-red-600">{error}</p>}

      <div className="mb-4 flex gap-4">
        <label className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 cursor-pointer disabled:opacity-50">
          {uploading ? "Uploading…" : "Upload PDF"}
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
        <input
          type="search"
          placeholder="Search documents…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && loadDocs()}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <button
          onClick={loadDocs}
          className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-50"
        >
          Search
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading documents…</p>
      ) : docs.length === 0 ? (
        <p className="text-gray-500">No documents.</p>
      ) : (
        <ul className="space-y-2">
          {docs.map((d) => (
            <li
              key={d.id}
              className="flex items-center justify-between rounded border border-gray-200 p-3"
            >
              <Link
                href={`/files/${d.id}`}
                className="font-medium text-blue-600 hover:underline"
              >
                {d.title}
              </Link>
              <label className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Inmate visible</span>
                <input
                  type="checkbox"
                  checked={d.inmate_visible}
                  onChange={() => toggleInmateVisible(d.id, d.inmate_visible)}
                  className="h-4 w-4"
                />
              </label>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

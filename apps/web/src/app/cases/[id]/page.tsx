"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/auth";
import * as api from "@/lib/api";
import { CASE_STATUSES, type CaseStatusValue, type Deadline } from "@/lib/api";
import { statusLabel } from "@/components/StatusBadge";

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
  const { user } = useAuth();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [deadlineTitle, setDeadlineTitle] = useState("");
  const [deadlineDueDate, setDeadlineDueDate] = useState("");
  const [deadlineNotes, setDeadlineNotes] = useState("");
  const [addingDeadline, setAddingDeadline] = useState(false);
  const [deadlineError, setDeadlineError] = useState("");

  const loadCase = useCallback(() => {
    if (!user) return;
    api.getCase(caseId).then(setCaseData).catch(setError);
  }, [user, caseId]);

  const loadDocs = useCallback(() => {
    if (!user) return;
    api
      .listCaseDocs(caseId, search || undefined)
      .then(setDocs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"))
      .finally(() => setLoading(false));
  }, [user, caseId, search]);

  const loadDeadlines = useCallback(() => {
    if (!user) return;
    api.listDeadlines(caseId).then(setDeadlines).catch(() => {});
  }, [user, caseId]);

  useEffect(() => {
    if (!user || !caseId) return;
    setLoading(true);
    loadCase();
    loadDocs();
    loadDeadlines();
  }, [user, caseId, loadCase, loadDocs, loadDeadlines]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadDoc(caseId, file, false);
      loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function toggleInmateVisible(docId: string, current: boolean) {
    if (!user) return;
    try {
      await api.updateDocInmateVisible(docId, !current);
      setDocs((prev) =>
        prev.map((d) =>
          d.id === docId ? { ...d, inmate_visible: !current } : d
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function handleStatusChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const status = e.target.value as CaseStatusValue;
    if (!caseData) return;
    setUpdatingStatus(true);
    setError("");
    try {
      await api.updateCaseStatus(caseId, status);
      setCaseData({ ...caseData, status });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setUpdatingStatus(false);
    }
  }

  async function handleAddDeadline(e: React.FormEvent) {
    e.preventDefault();
    if (!deadlineTitle.trim() || !deadlineDueDate) return;
    setAddingDeadline(true);
    setDeadlineError("");
    try {
      await api.createDeadline(caseId, deadlineTitle.trim(), deadlineDueDate, deadlineNotes.trim() || undefined);
      setDeadlineTitle("");
      setDeadlineDueDate("");
      setDeadlineNotes("");
      loadDeadlines();
    } catch (err) {
      setDeadlineError(err instanceof Error ? err.message : "Failed to add deadline");
    } finally {
      setAddingDeadline(false);
    }
  }

  async function handleDeleteDeadline(deadlineId: string) {
    try {
      await api.deleteDeadline(caseId, deadlineId);
      setDeadlines((prev) => prev.filter((d) => d.id !== deadlineId));
    } catch (err) {
      setDeadlineError(err instanceof Error ? err.message : "Failed to delete deadline");
    }
  }

  if (!caseData) return <div className="p-6">Loading…</div>;

  return (
    <div className="p-6">
      <Link href="/cases" className="mb-4 inline-block text-blue-600 hover:underline">
        ← Back to cases
      </Link>
      <div className="mb-2 flex items-center gap-3">
        <h1 className="text-xl font-semibold">{caseData.title}</h1>
        <select
          value={caseData.status}
          onChange={handleStatusChange}
          disabled={updatingStatus}
          className="rounded border border-gray-300 px-2 py-1 text-sm disabled:opacity-50"
        >
          {CASE_STATUSES.map((s) => (
            <option key={s} value={s}>
              {statusLabel(s)}
            </option>
          ))}
        </select>
      </div>
      {caseData.description && (
        <p className="mb-4 text-gray-600">{caseData.description}</p>
      )}
      {error && <p className="mb-2 text-red-600">{error}</p>}

      <section className="mb-6 rounded border border-gray-200 p-4">
        <h2 className="mb-3 font-medium">Deadlines</h2>
        {deadlineError && <p className="mb-2 text-sm text-red-600">{deadlineError}</p>}
        {deadlines.length === 0 ? (
          <p className="mb-3 text-sm text-gray-500">No deadlines yet.</p>
        ) : (
          <ul className="mb-3 space-y-1">
            {deadlines.map((d) => (
              <li key={d.id} className="flex items-center justify-between text-sm">
                <span>
                  <span className="font-medium">{d.due_date}</span> — {d.title}
                  {d.notes && <span className="text-gray-500"> ({d.notes})</span>}
                </span>
                <button
                  onClick={() => handleDeleteDeadline(d.id)}
                  className="text-xs text-red-600 hover:underline"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
        <form onSubmit={handleAddDeadline} className="flex flex-wrap items-end gap-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">Title</label>
            <input
              type="text"
              value={deadlineTitle}
              onChange={(e) => setDeadlineTitle(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">Due date</label>
            <input
              type="date"
              value={deadlineDueDate}
              onChange={(e) => setDeadlineDueDate(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-700">Notes (optional)</label>
            <input
              type="text"
              value={deadlineNotes}
              onChange={(e) => setDeadlineNotes(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={addingDeadline || !deadlineTitle.trim() || !deadlineDueDate}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {addingDeadline ? "Adding…" : "Add deadline"}
          </button>
        </form>
      </section>

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

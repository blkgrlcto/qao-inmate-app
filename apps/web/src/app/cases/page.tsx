"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
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
  const { user } = useAuth();
  const router = useRouter();
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const loadCases = () => {
    if (!user || user.role === "inmate") return;
    api
      .listCases()
      .then(setCases)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  };

  useEffect(loadCases, [user]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setCreating(true);
    setError("");
    try {
      await api.createCase(title.trim(), description.trim() || undefined);
      setTitle("");
      setDescription("");
      setShowForm(false);
      loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setCreating(false);
    }
  }

  useEffect(() => {
    if (user && user.role === "inmate") router.replace("/inmate");
  }, [user, router]);

  if (user?.role === "inmate") {
    return (
      <div className="p-6">
        <p className="text-gray-600">Staff only. Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Cases</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "New Case"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-6 rounded border border-gray-200 p-4"
        >
          <div className="mb-3">
            <label htmlFor="case-title" className="mb-1 block text-sm font-medium text-gray-700">
              Title
            </label>
            <input
              id="case-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2"
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="case-description" className="mb-1 block text-sm font-medium text-gray-700">
              Description (optional)
            </label>
            <textarea
              id="case-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2"
              rows={2}
            />
          </div>
          <button
            type="submit"
            disabled={creating || !title.trim()}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {creating ? "Creating…" : "Create case"}
          </button>
        </form>
      )}

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

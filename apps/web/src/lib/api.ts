// Same-origin proxy — the browser auto-attaches the httpOnly auth cookie here,
// and apiProxy/[...path]/route.ts forwards it as a Bearer header server-side.
const API_BASE = "/apiProxy";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};

export async function me(): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`);
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function listCases() {
  const res = await fetch(`${API_BASE}/cases`);
  if (!res.ok) throw new Error("Failed to fetch cases");
  return res.json();
}

export async function createCase(title: string, description?: string) {
  const res = await fetch(`${API_BASE}/cases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description: description || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Failed to create case");
  }
  return res.json();
}

export async function getCase(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}`);
  if (!res.ok) throw new Error("Failed to fetch case");
  return res.json();
}

export const CASE_STATUSES = ["open", "active", "awaiting_decision", "closed"] as const;
export type CaseStatusValue = (typeof CASE_STATUSES)[number];

export async function updateCaseStatus(caseId: string, status: CaseStatusValue) {
  const res = await fetch(`${API_BASE}/cases/${caseId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Failed to update status");
  return res.json();
}

export type Deadline = {
  id: string;
  title: string;
  due_date: string;
  notes: string | null;
};

export async function listDeadlines(caseId: string): Promise<Deadline[]> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/deadlines`);
  if (!res.ok) throw new Error("Failed to fetch deadlines");
  return res.json();
}

export async function createDeadline(caseId: string, title: string, dueDate: string, notes?: string) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/deadlines`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, due_date: dueDate, notes: notes || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Failed to add deadline");
  }
  return res.json();
}

export async function deleteDeadline(caseId: string, deadlineId: string) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/deadlines/${deadlineId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete deadline");
}

export async function listCaseDocs(caseId: string, q?: string) {
  const url = new URL(`${API_BASE}/cases/${caseId}/docs`, window.location.origin);
  if (q) url.searchParams.set("q", q);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function uploadDoc(caseId: string, file: File, inmateVisible: boolean) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/cases/${caseId}/docs?inmate_visible=${inmateVisible}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Upload failed");
  }
  return res.json();
}

export async function updateDocInmateVisible(docId: string, inmateVisible: boolean) {
  const res = await fetch(`${API_BASE}/files/${docId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inmate_visible: inmateVisible }),
  });
  if (!res.ok) throw new Error("Failed to update document");
  return res.json();
}

export async function listInmateDocs() {
  const res = await fetch(`${API_BASE}/docs/inmate`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export type SimilarResult = {
  id: string;
  citation: string;
  title: string;
  jurisdiction: string;
  date: string;
  disposition: string;
  score: number;
  headline?: string;
  pull_quotes?: string[];
  source_url?: string;
  why?: {
    keyword_matches?: string[];
    similarity_bucket?: "High" | "Medium" | "Low";
  };
};

export type FederalCaseResult = {
  id: string;
  external_docket_id: number;
  case_name: string | null;
  docket_number: string | null;
  court_id: string | null;
  date_filed: string | null;
  recap_available: boolean;
  absolute_url: string | null;
  detected_mode: string;
};

export async function searchFederalCases(params: {
  q: string;
  court_id?: string;
  limit?: number;
  cursor?: string;
}) {
  const url = new URL(`${API_BASE}/federal-cases/search`, window.location.origin);
  url.searchParams.set("q", params.q);
  if (params.court_id) url.searchParams.set("court_id", params.court_id);
  if (params.limit) url.searchParams.set("limit", String(params.limit));
  if (params.cursor) url.searchParams.set("cursor", params.cursor);
  const res = await fetch(url.toString());
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Search failed");
  }
  return res.json();
}

export async function searchSimilar(params: {
  q: string;
  jurisdiction?: string;
  disposition?: string[];
  limit?: number;
}) {
  const url = new URL(`${API_BASE}/similar`, window.location.origin);
  url.searchParams.set("q", params.q);
  if (params.jurisdiction) url.searchParams.set("jurisdiction", params.jurisdiction);
  if (params.disposition?.length)
    params.disposition.forEach((d) => url.searchParams.append("disposition", d));
  if (params.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString());
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Search failed");
  }
  return res.json();
}

// Admin

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
};

export async function adminListUsers(): Promise<AdminUser[]> {
  const res = await fetch(`${API_BASE}/admin/users`);
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
}

export async function adminCreateUser(input: {
  email: string;
  password: string;
  full_name: string;
  role: string;
}): Promise<AdminUser> {
  const res = await fetch(`${API_BASE}/admin/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Failed to create user");
  }
  return res.json();
}

export async function adminRevokeUserSessions(userId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/admin/users/${userId}/revoke`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to revoke sessions");
}

export type ShareRow = {
  id: string;
  case_id: string;
  user_id: string;
  role: string;
  user_email: string;
  user_full_name: string;
};

export async function adminListShares(caseId: string): Promise<ShareRow[]> {
  const url = new URL(`${API_BASE}/admin/shares`, window.location.origin);
  url.searchParams.set("case_id", caseId);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch shares");
  return res.json();
}

export async function adminCreateShare(input: {
  case_id: string;
  user_id: string;
  role: string;
}): Promise<ShareRow> {
  const res = await fetch(`${API_BASE}/admin/shares`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Failed to grant access");
  }
  return res.json();
}

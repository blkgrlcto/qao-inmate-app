const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE = `${API_URL}/api/v1`;

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Login failed");
  }
  return res.json();
}

export async function me(token: string): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function listCases(token: string) {
  const res = await fetch(`${API_BASE}/cases`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch cases");
  return res.json();
}

export async function getCase(token: string, id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch case");
  return res.json();
}

export async function listCaseDocs(token: string, caseId: string, q?: string) {
  const url = new URL(`${API_BASE}/cases/${caseId}/docs`);
  if (q) url.searchParams.set("q", q);
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function uploadDoc(
  token: string,
  caseId: string,
  file: File,
  inmateVisible: boolean
) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(
    `${API_BASE}/cases/${caseId}/docs?inmate_visible=${inmateVisible}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Upload failed");
  }
  return res.json();
}

export async function updateDocInmateVisible(
  token: string,
  docId: string,
  inmateVisible: boolean
) {
  const res = await fetch(`${API_BASE}/files/${docId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inmate_visible: inmateVisible }),
  });
  if (!res.ok) throw new Error("Failed to update document");
  return res.json();
}

export async function listInmateDocs(token: string) {
  const res = await fetch(`${API_BASE}/docs/inmate`, {
    headers: { Authorization: `Bearer ${token}` },
  });
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

export async function searchFederalCases(
  token: string,
  params: { q: string; court_id?: string; limit?: number; cursor?: string }
) {
  const url = new URL(`${API_BASE}/federal-cases/search`);
  url.searchParams.set("q", params.q);
  if (params.court_id) url.searchParams.set("court_id", params.court_id);
  if (params.limit) url.searchParams.set("limit", String(params.limit));
  if (params.cursor) url.searchParams.set("cursor", params.cursor);
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Search failed");
  }
  return res.json();
}

export async function searchSimilar(
  token: string,
  params: { q: string; jurisdiction?: string; disposition?: string[]; limit?: number }
) {
  const url = new URL(`${API_BASE}/similar`);
  url.searchParams.set("q", params.q);
  if (params.jurisdiction) url.searchParams.set("jurisdiction", params.jurisdiction);
  if (params.disposition?.length)
    params.disposition.forEach((d) => url.searchParams.append("disposition", d));
  if (params.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

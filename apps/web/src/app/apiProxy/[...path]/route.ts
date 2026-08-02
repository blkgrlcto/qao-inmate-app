import { NextRequest, NextResponse } from "next/server";
import { ACCESS_TOKEN_MAX_AGE, API_BASE, API_URL, AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, cookieOptions } from "@/lib/authCookies";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "POST");
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "PATCH");
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxy(request, params, "DELETE");
}

async function callBackend(
  target: string,
  method: string,
  headers: Record<string, string>,
  body?: ArrayBuffer
) {
  const init: RequestInit = { method, headers };
  if (body !== undefined) init.body = body;
  return fetch(target, init);
}

/** Exchange the refresh_token cookie for a new access token, or null if absent/invalid. */
async function tryRefresh(request: NextRequest): Promise<string | null> {
  const refreshToken = request.cookies.get(REFRESH_TOKEN_KEY)?.value;
  if (!refreshToken) return null;
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return null;
  const { access_token } = (await res.json()) as { access_token: string };
  return access_token;
}

async function proxy(
  request: NextRequest,
  params: Promise<{ path: string[] }>,
  method: string
) {
  const { path } = await params;
  const pathStr = path.join("/");
  const url = new URL(request.url);
  const target = `${API_URL}/api/v1/${pathStr}${url.search}`;

  const baseHeaders: Record<string, string> = {};
  request.headers.forEach((v, k) => {
    // content-length must NOT be forwarded verbatim — fetch() computes its own
    // for the outgoing body, and a stale value here can make the upstream
    // server see a truncated/empty body. authorization is excluded because we
    // set it explicitly below from the cookie, not whatever the browser sent.
    if (!["host", "cookie", "content-length", "authorization"].includes(k.toLowerCase())) {
      baseHeaders[k] = v;
    }
  });

  let body: ArrayBuffer | undefined;
  if (method !== "GET" && method !== "HEAD") {
    // Use arrayBuffer (not text) to preserve raw bytes for binary/multipart
    // bodies (e.g. PDF uploads) — text() would corrupt them via UTF-8 decoding.
    body = await request.arrayBuffer();
  }

  const token = request.cookies.get(AUTH_TOKEN_KEY)?.value;
  const headersWithAuth = (t?: string) => (t ? { ...baseHeaders, Authorization: `Bearer ${t}` } : baseHeaders);

  let res = await callBackend(target, method, headersWithAuth(token), body);

  // Access tokens are short-lived (30 min) by design — transparently refresh
  // and retry once on a 401 so users aren't logged out mid-session.
  let refreshedToken: string | null = null;
  if (res.status === 401 && pathStr !== "auth/refresh") {
    refreshedToken = await tryRefresh(request);
    if (refreshedToken) {
      res = await callBackend(target, method, headersWithAuth(refreshedToken), body);
    }
  }

  const contentType = res.headers.get("content-type") || "";
  // Pass the raw bytes straight through — parsing JSON here and handing the
  // resulting object to NextResponse would stringify it as "[object Object]"
  // instead of re-serializing it.
  const responseBody = await res.arrayBuffer();

  const responseHeaders: Record<string, string> = {
    "Content-Type": contentType,
  };
  const contentDisposition = res.headers.get("content-disposition");
  if (contentDisposition) responseHeaders["Content-Disposition"] = contentDisposition;

  const response = new NextResponse(responseBody, {
    status: res.status,
    headers: responseHeaders,
  });
  if (refreshedToken) {
    response.cookies.set(AUTH_TOKEN_KEY, refreshedToken, cookieOptions(request, ACCESS_TOKEN_MAX_AGE));
  }
  return response;
}

import { NextRequest, NextResponse } from "next/server";

// API_INTERNAL_URL is for server-side (this file runs in the Next.js server,
// not the browser) container-to-container calls; NEXT_PUBLIC_API_URL is
// host-facing and only correct here outside Docker where both coincide.
const API_URL =
  process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

async function proxy(
  request: NextRequest,
  params: Promise<{ path: string[] }>,
  method: string
) {
  const { path } = await params;
  const pathStr = path.join("/");
  const url = new URL(request.url);
  const target = `${API_URL}/api/v1/${pathStr}${url.search}`;
  const token = request.cookies.get("auth_token")?.value;

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  request.headers.forEach((v, k) => {
    // content-length must NOT be forwarded verbatim — fetch() computes its
    // own for the outgoing body, and a stale/duplicate value here can make
    // the upstream server see a truncated or empty body.
    if (!["host", "cookie", "content-length"].includes(k.toLowerCase())) {
      headers[k] = v;
    }
  });

  const init: RequestInit = {
    method,
    headers,
  };
  if (method !== "GET" && method !== "HEAD") {
    // Use arrayBuffer (not text) to preserve raw bytes for binary/multipart
    // bodies (e.g. PDF uploads) — text() would corrupt them via UTF-8 decoding.
    // content-type is already carried over by the forEach loop above — do NOT
    // set it again here under a differently-cased key ("Content-Type"), since
    // headers is a plain object and JS object keys are case-sensitive: that
    // previously produced two distinct content-type entries in the same request.
    init.body = await request.arrayBuffer();
  }

  const res = await fetch(target, init);
  const contentType = res.headers.get("content-type") || "";
  // Pass the raw bytes straight through — parsing JSON here and handing the
  // resulting object to NextResponse would stringify it as "[object Object]"
  // instead of re-serializing it.
  const body = await res.arrayBuffer();

  const responseHeaders: Record<string, string> = {
    "Content-Type": contentType,
  };
  const contentDisposition = res.headers.get("content-disposition");
  if (contentDisposition) responseHeaders["Content-Disposition"] = contentDisposition;

  return new NextResponse(body, {
    status: res.status,
    headers: responseHeaders,
  });
}
